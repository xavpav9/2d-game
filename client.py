import socket

ip = "127.0.0.1"
port = 2000

class Client:
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))
    
    def closeConnection(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


client = Client(ip, port)

client.closeConnection()
