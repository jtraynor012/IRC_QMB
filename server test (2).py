import socket
import select
import re
#import numpy

#COMMANDS = ['CAP', 'USER', 'NICK', 'JOIN', 'QUIT']


class Server():
	def __init__(self):
		#initializing all command vars
		self.channels = []
		self.hostname = "QMB_IRC_SERVER"
		self.HOST = "fc00:1337::17"
		#self.HOST = "::1"
		self.PORT = 6667

		#done like this purely for the select and lazyness in this case
		self.client_socket_list = []
		self.client_list = []
		return
		
	#main loop of the server
	def mainLoop(self):
		#setting up the server socket
		server_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
		server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_sock.bind((self.HOST, self.PORT))
		server_sock.listen()
		
		#Called client list but first socket is the server. Means one for loop instead of splitting it up
		self.client_socket_list.append(server_sock)
		while True:
			#sets up polling and returns array of sockets with incomming messages
			readList, writeList, error_sockets = select.select(self.client_socket_list,[],[])
			#loops all incomming sockets
			for sock in readList:
				#checks for new clients
				if sock == server_sock:
					client, address = server_sock.accept()
					self.client_socket_list.append(client)
					self.client_list.append(Client(client, address))
					############
					############ fix this print
					############
					#print(f'{client} connected --> {data.encode()}')
				else:
					self.commands(sock)
		return

	#parses most input for commands		
	def commands(self, client_socket):
		client = self.findClient(client_socket)
		incoming = []
		data = client_socket.recv(1024).decode()
		#dev for checking whats happening server side
		print(f'{client_socket} --> {data.encode()}')
		incoming.append(data.splitlines())
		line = incoming.pop(0)
		for i in line:
			cmd = i.split(' ')
			#checks for the nick command
			if cmd[0] == "NICK":
				self.nick(cmd, client)
			#checks for user
			elif cmd[0] == "USER":
				self.user(cmd, client)
			#checks for join
			elif cmd[0] == "JOIN":
				self.join(cmd, client)
			#checks for quit
			elif cmd[0] == "QUIT":
				self.leave(client)
			#checks for privmsg
			elif cmd[0] == "PRIVMSG":
				self.privmsg(cmd, client)
			elif cmd[0] == "WHO":
				self.who(cmd, client)
			elif cmd[0] == "PART":
				self.leaveChannel(cmd, client)
			#unknown commands
			else:
				self.socketMessage(client, f':{self.hostname} 421 {client.getNick()} {cmd[0]} :Unknown command\r\n'.encode())
		return

	#handles the nick command
	def nick(self, cmd, client):
		#no nickname given
		if len(cmd) < 2:
			self.socketMessage(client, f':{self.hostname} 431 {client.getNick()} :No nickname given\r\n'.encode())
		else:
			#checks for illegal nicks
			###########
			########### this regex needs to be corrected
			###########
			x = True#re.search("[a-zA-Z0-9]+", cmd[1])
			
			if x:
				
				#checks for duplicates
				if any(item.getNick() == cmd[1] for item in self.client_list):
					#duplicate nick
					
					self.socketMessage(client, f':{self.hostname} 433 {client.getNick()} {cmd[1]} :Nickname is already in use\r\n'.encode())
				else:
					client.setNick(cmd[1])
					if client.getUser() != "":
						client.setRegistered()
						self.registerMessage(client)
			else:
				#ilegal nick
				self.socketMessage(client, f':{self.hostname} 432 {client.getNick()} {cmd[1]} :Erroneous nickname\r\n'.encode())
		return

	#handles the user command
	def user(self, cmd, client):
		#checks there is enough params
		if len(cmd) < 5:
			self.socketMessage(client, f':{self.hostname} 461 {client.getNick()} {cmd[0]} :Not enough parameters\r\n'.encode())
		#checks not already registered
		elif client.getRegistered():
			self.socketMessage(client, f':{self.hostname} 462 {client.getNick()} :Unauthorized command (already registered)\r\n'.encode())
		else:
			cmd.pop(0)
			client.setUser(cmd.pop(0))
			client.setMode(cmd.pop(0))
			cmd.pop(0)
			client.setRealname(cmd.pop(0)[1:])
			for name in cmd:
				client.setRealname(client.getRealname() + name)
			if client.getNick() != "*":
				client.setRegistered()
				self.registerMessage(client)
		return

	#handles the join command
	def join(self, cmd, client):
		# leaves all channels
		if cmd[1] == "0":
			self.leaveAllChannels(client)
			return
		args = cmd[1].split(",")
		for argument in args:
			###########
			########### need to check argument formatting
			###########
			if not self.channels:
				self.channels.append(Channel(argument, client))
				if self.channels[0].getTopic() == "":
					self.socketMessage(client, f':{client.getNick()} JOIN {argument}\r\n'.encode())
					self.socketMessage(client, f':{self.hostname} 331 {client.getNick()} {cmd[1]} :No topic is set\r\n'.encode())
				else:
					self.socketMessage(client, f':{client.getNick()} JOIN {argument}\r\n'.encode())
					self.socketMessage(client, f':{self.hostname} 332 {client.getNick()} {cmd[1]} :{argument}\r\n'.encode())
				nameList = ""
				for client in self.channels[0].getClients():
					nameList = " " + nameList + client.getNick()
					nameList = nameList[1:]
				self.socketMessage(client, f':{self.hostname} 353 {self.channels[0].getName()} :{nameList}\r\n'.encode())
			else:
				for channel in self.channels:
					#if channel exists join it
					if argument == channel.getName():
						channel.addClient(client)
						if channel.getTopic() == "":
							self.socketMessage(client, f':{client.getNick()} JOIN {channel.getName()}\r\n'.encode())
							self.socketMessage(client, f':{self.hostname} 331 {client.getNick()} {cmd[1]} :No topic is set\r\n'.encode())
						else:
							self.socketMessage(client, f':{client.getNick()} JOIN {channel.getName()}\r\n'.encode())
							self.socketMessage(client, f':{self.hostname} 332 {client.getNick()} {cmd[1]} :{channel.getTopic()}\r\n'.encode())
					nameList = ""
					for client in channel.getClients():
						nameList = " " + nameList + client.getNick()
						nameList = nameList[1:]
					self.socketMessage(client, f':{self.hostname} 353 {channel.getName()} :{nameList}\r\n'.encode())
		return
	############
	############ need to find the error message to send
	############
	#handles the quit command
	def leave(self, client):
		print("quit")
		return

	#handles the privmsg command ie chat
	############
	############ this needs implemented
	############
	def privmsg(self, cmd, client):
		print("privmsg")
		return
	
	def who(self, cmd, client):

		print("who")
		"""
		if len(cmd) == 1 or cmd[1] == "0":
			noLinkClients = self.client_list.copy()
			for channel in self.channels:
				if client in channel:
					for other in channel:
						if other in noLinkClient:
							noLinkClient.remove(other)
							"""
							
					
						
		#else:
			#self.socketMessage(client, f':{self.hostname} 352 {client.getName()} :{nameList}\r\n'.encode())
		return

	###########
	########### this needs implemented
	###########
	# this makes the client leave the channel
	def leaveChannel(self, cmd, client, channel):
		if client in channel.getClients():
		#remove client from channel; and reply confirm
			cmd[1].removeClient(client)
			self.socketMessage(client, f':{client.nick}!{client.user}@{self.hostname} PART #{cmd[1].getName()} :\r\n'.encode())
		else:
			#ERR_NOTONCHANNEL
			self.socketMessage(client, f'{client.nick}!{client.user}@{self.hostname} <{cmd[1].getName}> :You\'r not on that channel.')
		return

	#calls leave channel to leave all channels
	def leaveAllChannels(self, client):
		for channel in self.channels:
			if client.getSocket() in channel.getClients():
				self.leaveChannel(client, channel)
		return
	
	#message everone on server
	def messageAll(self, client, message):
		for socket in self.client_socket_list:
			if socket != self.HOST and socket != client.getSocket:
				try:
					self.socketMessage(socket, message)
				except:
					self.removeClient(client)
		return

	#messages everyone selected other than the user, this is used for channels
	def messageSelect(self, sender, message, clients):
		for client in clients:
			if client.getSocket() != self.client_socket_list[0].getSocket() and client.getSocket() != sender.getSocket():
				try:
					self.socketMessage(client, message)
				except:
					self.removeClient(client)
		return

	#sends a message to the client
	def socketMessage(self, client, msg):
		client.getSocket().send(msg)
		print(f'{client.getAddress()} <-- {msg}')
		return


	#removes a client from the server and all channels
	def removeClient(self, client):
		self.leaveAllChannels(client)
		client.getSocket().close()
		self.client_socket_list.remove(client.getSocket())
		self.client_list.remove(client)
		del client
		return

	#finds the client object given the client socket
	def findClient(self, sock):
		for client in self.client_list:
			if client.getSocket() == sock:
				return client
		return False

	#sends the registered reply message
	def registerMessage(self, client):
		self.socketMessage(client, f':{self.hostname} 001 {client.getNick()} :Hi, Welcome to IRC\r\n'.encode())
		self.socketMessage(client, f':{self.hostname} 002 {client.getNick()} :Your host is {self.hostname}\r\n'.encode())
		self.socketMessage(client, f':{self.hostname} 003 {client.getNick()} :There are {len(self.client_list)} users on 1 server\r\n'.encode())
		self.socketMessage(client, f':{self.hostname} 004 {client.getNick()} :{self.hostname} miniircd-2.1 o o\r\n'.encode())
		return
		

#contains all the information about individual clients
class Client():
	def __init__(self, sock_obj, client_address):
		self.sock = sock_obj
		self.address = client_address
		self.nick = "*"
		self.user = ""
		self.mode = 0
		self.realname = ""
		self.registered = False
		return

	def getSocket(self):
		return self.sock

	def getAddress(self):
		return self.address

	def getNick(self):
		return self.nick

	def getUser(self):
		return self.user

	def getRealname(self):
		return self.realname

	def getRegistered(self):
		return self.registered

	def setNick(self, setNick):
		self.nick = setNick
		return

	def setUser(self, setUser):
		self.user = setUser
		return

	def setMode(self, setMode):
		self.mode = setMode
		return

	def setRealname(self, setName):
		self.realname = setName
		return

	def setRegistered(self):
		self.registered = True
		return

#contains all the information about individual channels
class Channel():
	def __init__(self, newName, client):
		self.topic = ""
		self.clients = [client]
		self.name = newName
		return

	def getTopic(self):
		return self.topic

	def getClients(self):
		return self.clients

	def getName(self):
		return self.name

	def setTopic(self, newTopic):
		self.topic = newTopic
		return

	def addClient(self, client):
		self.clients.append(client)
		return

	def deleteClient(slef, client):
		self.clients.remove(client)
	
#runs the server
serv = Server()
serv.mainLoop()	
