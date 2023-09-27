class Client:
	nickname = ""
	username = ""
	addr = ""
	conn = ""

	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr

