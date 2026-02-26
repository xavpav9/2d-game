import socket

ip = "127.0.0.1"
port = 2000

class Client:
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))
        self.headersize = int(self.sock.recv(8).decode(encoding="utf-8"))

    def sendData(self, data):
        encodedData = data.encode(encoding="utf-8")
        dataLength = len(encodedData)
        formattedData = f"{dataLength:<{self.headersize}}".encode(encoding="utf-8") + encodedData
        self.sock.send(formattedData)

    def recvData(self):
        try: dataLength = int(self.sock.recv(self.headersize).decode(encoding="utf-8"))
        except: return ""

        data = ""
        for i in range(dataLength // 8):
            newData = self.sock.recv(8)
            data += newData.decode(encoding="utf-8")
        if dataLength % 8 != 0:
            newData = self.sock.recv(dataLength % 8)
            data += newData.decode(encoding="utf-8")

        return data
    
    def close(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


client = Client(ip, port)

client.sendData("hello back")
print(client.recvData())

client.close()
