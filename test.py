import socket

with open('example_request_1.json', 'rb') as f:
	request = f.read()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.connect(('142.93.137.62', 31337))
s.connect(('127.0.0.1', 31337))
s.send(request)
print("[+] Sent request")
print(s.recv(2**16))
