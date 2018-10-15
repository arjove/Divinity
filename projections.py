
import json
import requests
import socket
import threading
import googlemaps
import pickle
import os
import datetime
import sys

from secrets import GOOGLE_API_KEY

gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

AREAS = 'Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot'

def walk(directions, seconds):
	for step in directions[0]['legs'][0]['steps']:
		if seconds - step['duration']['value'] < 0:
			# Returns current step, 0 remaining seconds, and part of current step that is completed
			return step, 0, seconds / step['duration']['value']
		seconds -= step['duration']['value']
	# Returns remaining seconds
	return None, seconds, 0

def handle_connection(client_socket, address, group_info, graph):
	print("[+] Handing connection from " + address[0])
	data = client_socket.recv(1024)

	if data:
		request = json.loads(data)
		process(client_socket, request, group_info, graph)

	client_socket.close()

def get_and_store_group_info():
	print("[!] Updating group info...")
	api_url = "https://www.eej.moe/api/{0}".format("group")

	response = requests.get(api_url, timeout=(1,1))

	if response.status_code == 200:
		print('[+] Finished updating group info')
		print("[!] Storing group info to file group_info.dat")
		with open('group_info.dat', 'wb') as f:
			pickle.dump(response.json(), f)
		print("[+] Completed storing group info")
		return response.json()
	else:
		print("[-] Failed updating group info")
		return None

# Set graph such that graph[area][x][y] = route from group x to group y
def build_and_store_graph(group_info):
	print("[!] Building complete graph of routes for each subarea...")
	graph = {}
	max_group_id = max([group['id'] for group in group_info])

	for area in AREAS:
		print("[!] Building graph for area " + area)
		groups = [group for group in group_info  if group['Subarea']['name'] == area]
		graph[area] = [[None for _ in range(max_group_id + 1)] for _ in range(max_group_id + 1)]
		
		for i, x in enumerate(groups):
			for j, y in enumerate(groups):
				if i > j:
					directions_result = gmaps.directions(x['location'], y['location'], mode="walking", alternatives="true")
					graph[area][i][j] = directions_result
					graph[area][j][i] = directions_result
					print(x['name'], '\t', y['name'], '\t', directions_result[0]['legs'][0]['distance'])
	
	print("[+] Graph completed")

	print("[!] Storing graph to file graph.dat")
	with open('graph.dat', 'wb') as f:
		pickle.dump(graph, f)
	print(["[+] Completed storing graph"])

# Creates distance list to groups in the subarea
def group_dist(location, group_info, area):
	distances = []

	for group in group_info:
		if group['Subarea']['name'] != area:
			continue

		directions_result = gmaps.directions(origin=location,
			destination = group['location'],
			mode = "walking",
			alternatives = "true")

		distances.append((group, directions_result))

	return distances

def process(socket, request, group_info, graph):
	# Dictionary that contains an entry of following format per group
	# [waypoint_groups, next group, current_step, step_progress]
	projections = {}

	# List of groups that have been visited
	visited = []

	for entry in request['lastLocations']:
		# List of groups visited after previous known location
		waypoints = []

		area = entry['subarea'].capitalize()
		print('[!] Area:', area)
		# Elapsed time since last seen
		seconds = (datetime.datetime.now() - datetime.datetime.fromisoformat(entry['timestamp'][:-1])).total_seconds()
		seconds = 2000
		print('[!] Time since last seen:', seconds, 'sec')

		distances = group_dist(entry['location'], group_info, area)
		distances.sort(key=lambda x : x[1][0]['legs'][0]['distance']['value'])
		nearest = [el for el in distances if el[0] not in visited][0]

		while seconds > 0:
			cur_step, seconds, step_progress = walk(nearest[1], seconds)
			if cur_step is not None:
				projections[area] = [waypoints, nearest[0], cur_step, step_progress]
				continue

			visited.append(nearest[0])
			waypoints.append(nearest[0])

			distances = group_dist((nearest[0]['latitude'], nearest[0]['longitude']), group_info, area)
			distances.sort(key=lambda x : x[1][0]['legs'][0]['distance']['value'])
			nearest = [el for el in distances if el[0] not in visited][0]

		print('[+] Estimated current location')

	print('[!] Sending projections')
	socket.send(json.dumps(projections).encode('utf-8'))
	print('[+] Projections sent')
		
def main():
	# Start listening on port 31337
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(("0.0.0.0", 31337))
	s.listen(5);

	# Create or load group info
	if os.path.exists('group_info.dat'):
		print('[!] group_info.dat exists. Loading file...')
		with open('group_info.dat', 'rb') as f:
			group_info = pickle.load(f)
		print("[+] Completed loading group info")
	else:
		print("[!] group_info.dat does not exist")
		group_info = get_and_store_group_info()

	# Create or load graph
	if os.path.exists('graph.dat'):
		print("[!] graph.dat exists. Loading file...")
		with open('graph.dat', 'rb') as f:
			graph = pickle.load(f)
		print("[+] Completed loading graph")
	else:
		print("[!] graph.dat does not exist")
		graph = build_and_store_graph(group_info)

	while True:
		(client_socket, address) = s.accept()
		client_socket.settimeout(60)
		threading.Thread(target = handle_connection, args=(client_socket, address, group_info, graph)).start()

if __name__ == "__main__":
	main()
