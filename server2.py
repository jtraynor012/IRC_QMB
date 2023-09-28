import socket

HOST_NAME = "QMB_IRC_SERVER"
HOST = "fc00:1337::17"
PORT = 6667

nickname = ""
username = ""



with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind((HOST, PORT))
	s.listen()

	client_socket, client_addr = s.accept()
	print(f'{client_addr} has connected to the server...')




	incoming = []
	while True:
		data = client_socket.recv(1024).decode()
		print(f'{client_addr} --> {data.encode()}')

		s.setblocking(0)

		if not data:
			break

		incoming.append(data.splitlines())

		#if input buffer has input
		if len(incoming) >= 1:

			#take first thing from front of buffer
			cmd = incoming.pop(0)

			##split by whitespace and extract commands + operands
			for i in cmd:
				comm = i.split(' ')
				if comm[0] == "NICK":
					nickname = comm[1]

					#print(nickname)
				if comm[0] == "USER":
					username = comm[1]
					#print(username)
		if nickname and username:

			welcome_msg = []
			welcome_msg.append(f':{HOST_NAME} 001 {nickname} :Hi, Welcome to IRC\r\n'.encode())
			welcome_msg.append(f':{HOST_NAME} 002 {nickname} :Your host is {HOST_NAME}\r\n'.encode())
			welcome_msg.append(f':{HOST_NAME} 003 {nickname} :There are 1 users and 0 services on 1 server\r\n'.encode())
			welcome_msg.append(f':{HOST_NAME} 004 {nickname} :{HOST_NAME} miniircd-2.1 o o\r\n'.encode())


			#sending welcome messages -> IS NOT WORKING AT ALL		
			client_socket.send(welcome_msg[0])
			print(f'{client_addr} <-- {welcome_msg[0]}')
			client_socket.send(welcome_msg[1])
			print(f'{client_addr} <-- {welcome_msg[1]}')
			client_socket.send(welcome_msg[2])
			print(f'{client_addr} <-- {welcome_msg[2]}')
			client_socket.send(welcome_msg[3])
			print(f'{client_addr} <-- {welcome_msg[3]}')