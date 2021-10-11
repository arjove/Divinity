
import json, requests, socket
import os, sys, threading
import pickle, signal, datetime
import googlemaps
from cachetools import cached, LRUCache
from cachetools.keys import hashkey

gmaps = googlemaps.Client(key=os.environ.get('GOOGLE_SERVER_AUTH_TOKEN'))

AREAS = 'Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot'

cache = LRUCache(maxsize=2**16)

def signal_handler(sig, frame):
	print("\n[!] Caught SIGINT. Storing cache and quitting...")
	with open("cache.dat", 'wb') as f:
		pickle.dump(cache, f)
	print("[+] Completed storing cache. Bye!")
	sys.exit(0)

def direction_key(*args, **kwargs):
	return str(args)

def walk(directions, seconds):
	polylines = []
	for step in directions[0]['legs'][0]['steps']:
		polylines.append(step['polyline']['points'])
		if seconds - step['duration']['value'] < 0:
			# Returns current step, 0 remaining seconds, and part of current step that is completed
			return step, polylines, 0, seconds / step['duration']['value']
		seconds -= step['duration']['value']
	# Returns remaining seconds
	return None, polylines, seconds, 0

def handle_connection(client_socket, address, group_info):
	print("[+] Handing connection from " + address[0])
	data = client_socket.recv(1024)

	if data:
		request = json.loads(data)
		process(client_socket, request, group_info)

	client_socket.close()

def get_group_info():
	print("[!] Updating group info...")
	api_url = "http://{0}/api/group".format(os.environ.get('JOTIHUNT_HOST'))

	response = requests.get(api_url, timeout=(1,1))

	if response.status_code == 200:
		print('[+] Finished updating group info')
		return response.json()
	else:
		print("[-] Failed updating group info")
		return None

@cached(cache, key=direction_key)
def group_dist(location, area_groups):
	distances = []

	for group in area_groups:
		directions_result = gmaps.directions(origin=location,
			destination = group['location'],
			mode = "walking",
			alternatives = "true")

		distances.append((group, directions_result))

	return distances


# Creates distance list to groups in the subarea
def group_dist_wrapper(location, group_info, area):
	return group_dist(location, [group for group in group_info if group['Subarea']['name'] == area])

def process(socket, request, group_info_param):
	# List of options
	projections = []

	# Project location for 3 nearest groups
	for target in range(3):
			# Create a copy of group_info_param
			group_info = group_info_param[:]
			# Dictionary that contains an entry of following format per group
			# [waypoint_groups, next group, current_step, step_progress, polylines]
			option = {}

			# Number of visits per group
			visited = [group['visits'] for group in group_info]

			for entry in request['lastLocations']:
				# List of groups visited after previous known location
				waypoints = []
				# List of lines that are on the travelled and future path
				polylines = []

				area = entry['subarea'].capitalize()
				print('[!] Area:', area)
				# Elapsed time since last seen
				seconds = (datetime.datetime.now() - datetime.datetime.fromisoformat(entry['timestamp'][:-1])).total_seconds()
				print('[!] Time since last seen:', seconds, 'sec')

				try:
					distances = group_dist_wrapper(entry['location'], group_info, area)
					distances.sort(key=lambda x : x[1][0]['legs'][0]['distance']['value'])
					nearest = [el for el in distances if el[0]['visits'] == min(visited)][target]

					while seconds > 0:
						cur_step, lines, seconds, step_progress = walk(nearest[1], seconds)
						polylines += lines
						if cur_step is not None:
							# We are not at our destination and time's up
							option[area] = [waypoints, nearest[0], cur_step, step_progress, polylines]
						else:
							# We are at our destination and there is time left
							visited[group_info.index(nearest[0])] += 1 # In list of visit numbers, increment visited group

							# Append visisted group to waypoints
							nearest[0]['visits'] += 1
							waypoints.append(nearest[0])

							# Increment value in group_info
							group_info[group_info.index(nearest[0])]['visits'] += 1

							# Compute new path from visited group to next nearest group
							distances = group_dist_wrapper((nearest[0]['latitude'], nearest[0]['longitude']), group_info, area)
							distances.sort(key=lambda x : x[1][0]['legs'][0]['distance']['value'])
							nearest = [el for el in distances if el[0]['visits'] == min(visited)][0]

				except Exception as e:
					print("[-] Something wrent wrong. Skipping this target. Error:", e)
					option[area] = None
					continue

			projections.append([option])

			print('[+] Estimated current location')

	print('[!] Sending projections')
	socket.sendall(json.dumps(projections).encode('utf-8'))
	print('[+] Projections sent')

def main():
	# Start listening on port 31337
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(("0.0.0.0", 31337))
	s.listen(5);

	# Attempt to load cache
	if os.path.exists('cache.dat'):
		print("[!] cache.dat exists. Loading file...")
		with open('cache.dat', 'rb') as f:
			cache = pickle.load(f)
		print("[+] Completed loading cache")
	else:
		print("[!] cache.dat does not exist: using new cache.")

	# Handler that saves the cache in case of interrupt
	signal.signal(signal.SIGINT, signal_handler)

	while True:
		(client_socket, address) = s.accept()
		client_socket.settimeout(60)
		group_info = get_group_info()
		threading.Thread(target = handle_connection, args=(client_socket, address, group_info)).start()


if __name__ == "__main__":
	main()
