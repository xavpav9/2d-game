import socket, select, json, random
from game import Game
from threading import Thread

ip = "0.0.0.0"
port = 2000

class Server:
    def __init__(self, ip, port, headersize, gameHandler):
        self.headersize = headersize
        self.gameHandler = gameHandler

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.listen(5)

        self.conns = []
        self.connNames = [self.sock]

    def sendData(self, conn, data):
        """
        prefix:
            s = serverData
            p = playerData
            d = disconnect
            a = alert
        """
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
        for otherConn in self.connNames:
            if otherConn not in connsToAvoid and otherConn != self.sock:
                self.sendData(otherConn, data)

    def acceptConnection(self):
        conn, addr = self.sock.accept()
        conn.send(str(self.headersize).encode(encoding="utf-8"))
        username = self.recvData(conn).strip()
        self.sendData(conn, "s" + json.dumps(gameHandler.serverData))

        valid = True
        problems = []
        for otherConn in self.conns:
            if otherConn["username"] == username:
                problems.append("Username in use.")
                valid = False
                break

        if len(username) < 2 or len(username) > 15:
            valid = False
            problems.append("Username must be between 2 and 15 characters long.")

        if valid:
            self.conns.append({"conn": conn, "addr": addr, "username": username})
            self.connNames.append(conn)

            print(f"New connection at {addr}")
            return conn
        else:
            self.sendData(conn, "d" + json.dumps(problems))
            self.removeConnection(conn)
            return False

    def removeConnection(self, conn):
        for i in range(len(self.conns)):
            if self.conns[i]["conn"] == conn:
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                except: pass

                print(f"Removed connection at {self.conns[i]['addr']}")

                self.conns.pop(i)
                self.connNames.pop(i+1)
                self.gameHandler.removePlayer(i)
                break

    def automaticLoop(self, running):
        while running[0]:
            connsToRead, _, connsInError = select.select(self.connNames, [], self.connNames)

            for conn in connsInError:
                self.removeConnection(conn)

            for conn in connsToRead:
                if conn == self.sock:
                    newConn = self.acceptConnection()
                    if newConn != False: gameHandler.addPlayer(self.conns[-1])
                else:
                    data = self.recvData(conn)
                    gameHandler.handleData(data, self.conns[self.connNames.index(conn) - 1])

                    if data == "": self.removeConnection(conn)

    def close(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

if __name__ == "__main__":


    features = []
    mapSize = [1000, 1200]
    maxFeatureHeight = 200
    for i in range(2, (mapSize[1] - maxFeatureHeight) // 100 + 1):
        rockWidth = random.randint(20, 40)
        rockHeight = rockWidth + random.randint(-2, 2)
        bushWidth = random.randint(80, 160)
        bushHeight = bushWidth // 2 + random.randint(-2, 2)

        features.append({"name": "rock", "position": [random.randint(0, mapSize[0] - rockWidth), i * 100 + random.randint(-80, 80)], "size": [rockWidth, rockHeight], "collides": True})
        features.append({"name": "bush", "position": [random.randint(0, mapSize[0] - bushWidth), i * 100 + random.randint(-80, 80)], "size": [bushWidth, bushHeight], "collides": False})


    gameHandler = Game([], {"map": mapSize, "player": {"defaultSize": [30, 30]}, "features": features})
    server = Server(ip, port, 8, gameHandler)
    gameHandler.addServer(server)


    running = [True]
    tGameLoop = Thread(target=gameHandler.tick, args=[running, ])
    tGameLoop.start()
    server.automaticLoop(running)

    running[0] = False
    server.close()
    tGameLoop.join()
