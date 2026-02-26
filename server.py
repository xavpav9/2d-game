import socket, select

ip = "0.0.0.0"
port = 2000

class Server:
    def __init__(self, ip, port, headersize):
        self.headersize = headersize

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.listen(5)

        self.conns = []
        self.conn_names = [self.sock]

    def sendData(self, conn, data):
        encodedData = data.encode(encoding="utf-8")
        dataLength = len(encodedData)
        formattedData = f"{dataLength:<{self.headersize}}".encode(encoding="utf-8") + encodedData
        conn.send(formattedData)

    def recvData(self, conn):
        try: dataLength = int(conn.recv(self.headersize).decode(encoding="utf-8"))
        except: return ""

        data = ""
        for i in range(dataLength // 8):
            newData = conn.recv(8)
            data += newData.decode(encoding="utf-8")
        if dataLength % 8 != 0:
            newData = conn.recv(dataLength % 8)
            data += newData.decode(encoding="utf-8")

        return data
    
    def distributeData(self, data, connsToAvoid=[]):
        for otherConn in self.conn_names:
            if otherConn not in connsToAvoid and otherConn != self.sock:
                self.sendData(otherConn, data)

    def acceptConnection(self):
        conn, addr = self.sock.accept()
        conn.send(str(self.headersize).encode(encoding="utf-8"))
        self.conns.append({"conn": conn, "addr": addr})
        self.conn_names.append(conn)

        print(f"New connection at {addr}")
        return conn

    def removeConnection(self, conn):
        for i in range(len(self.conns)):
            if self.conns[i]["conn"] == conn:
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                except: pass

                print(f"Removed connection at {self.conns[i]['addr']}")

                self.conns.pop(i)
                self.conn_names.pop(i+1)
                break

    def automaticLoop(self, running):
        while running[0]:
            connsToRead, _, connsInError = select.select(self.conn_names, [], self.conn_names)

            for conn in connsInError:
                self.removeConnection(conn)

            for conn in connsToRead:
                if conn == self.sock:
                    newConn = self.acceptConnection
                else:
                    data = self.recvData(conn)
                    print(data)
                    if data == "": self.removeConnection(conn)
                    else:
                        self.distributeData(data, [])

    def close(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


server = Server(ip, port, 8)

conn = server.acceptConnection()

running = [True]
server.automaticLoop(running)

server.close()
