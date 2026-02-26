import socket

ip = "0.0.0.0"
port = 2000

class Server:
    def __init__(self, ip, port):

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.listen(5)

        self.conns = []
        self.conn_names = [self.sock]

    def acceptConnection(self):
        conn, addr = self.sock.accept()
        self.conns.append({"conn": conn, "addr": addr})
        self.conn_names.append(conn)

        print(f"New connection at {addr}")
        return conn

    def removeConnection(self, conn):
        for i in range(len(self.conns)):
            if self.conns[i]["conn"] == conn:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()

                self.conns.pop(i)
                self.conn_names.pop(i+1)
                break


server = Server(ip, port)

conn = server.acceptConnection()
server.removeConnection(conn)
