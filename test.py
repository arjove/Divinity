import socket

with open('example_request.json', 'rb') as f:
	request = f.read()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 31337))
s.send(request)
print("[+] Sent request")
print(s.recv(2**12))