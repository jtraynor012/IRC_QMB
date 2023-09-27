import socket
import client_mod
import re
from _thread import *
import threading

HOST_NAME = "QMB_IRC_SERVER"
HOST = "fc00:1337::17"
PORT = 6667

USERS = []

COMMANDS = ['CAP', 'USER', 'NICK']

#Server command functions
def cap(arg, client):
	print(" ")
def user(username, client):
	client.username = username
def nick(nickname, client):
	client.nickname = nickname



disp_table = {
	'CAP': cap,
	'USER': user,
	'NICK': nick,

}

#>>>>>>>
# CAP LS 302 - ignore
# NICK nickname
# USER username 0 * :realname

#<<<<<<<
# :Server 001 nickname :Welcome message <nick>!<user>@host
# :Server 002 nickname :your host message
# :Server 003 nickname :Created message
# :Server 004 nickname :<servername> <version> <usermodes> <channelmodes>

def hold_client(client):
	print('Here!')
	## >> THIS PART ISNT SENDING TO THE CLIENT << ##
		client.conn.send(b':{HOST_NAME} 001 {client.nickname} :Hi, Welcome to IRC')
		client.conn.send(b':{HOST_NAME} 002 {client.nickname} :Your host is {HOST_NAME}')
		client.conn.send(b':{HOST_NAME} 003 {client.nickname} :There are 1 users and 0 serviceson 1 server')
		client.conn.send(b':{HOST_NAME} 004 {client.nickname} :{HOSTNAME} miniircd-2.1 o o')
			

def init_client(conn_, addr_):
	# create client object for this connection
	client = client_mod.Client(conn_, addr_)

	USERS.append(client)

	# debug - remove for finished product
	print(f'Connected by {addr_}')

	# input buffer
	incoming = []

	while not client.nickname and not client.username:
		# take input from client, decode it from bytecode and split it
		# by the special chars
		data = conn_.recv(1024).decode()
		incoming.append(data.splitlines())

		#if input buffer has input
		if len(incoming) >= 1:

			#take first thing from front of buffer
			cmd = incoming.pop(0)

			##split by whitespace and extract commands + operands
			for i in cmd:
				comm = i.split(' ')
				if comm[0] in COMMANDS:
					disp_table[comm[0]](comm[1], client)

		if not data:
			break
		print('line 79')
		conn_.send(b'Hello')
		if client.username:
			#once username has been stored, move over to hold_client function
			hold_client(client)

with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind((HOST, PORT))
	s.listen()

	while True:
		conn, addr = s.accept()
		client_thread = threading.Thread(target=init_client, args=[conn,addr])
		client_thread.start()
