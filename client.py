import socket

class Client:
    def __init__(self, ip, port, username):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))
        self.headersize = int(self.sock.recv(8).decode(encoding="utf-8"))
        self.sendData(username)

    def sendData(self, data):
        encodedData = data.encode(encoding="utf-8")
        dataLength = len(encodedData)
        formattedData = f"{dataLength:<{self.headersize}}".encode(encoding="utf-8") + encodedData
        self.sock.send(formattedData)

    def recvData(self, decode=True):
        try: dataLength = int(self.sock.recv(self.headersize).decode(encoding="utf-8"))
        except: return ""

        encodedData = b""
        for i in range(dataLength // 8):
            newData = self.sock.recv(8)
            encodedData += newData
        if dataLength % 8 != 0:
            newData = self.sock.recv(dataLength % 8)
            encodedData += newData

        if decode: return encodedData.decode("utf-8")
        else: return encodedData
    
    def close(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 2000

    client = Client(ip, port, "Player_1")

    client.sendData("hello back")
    print(client.recvData())

    client.close()
