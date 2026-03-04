import json, display, random
from client import Client
from threading import Thread

ip = "127.0.0.1"
port = 2000

def handleServer(client, playerData, serverData):
    while True:
        data = client.recvData()
        if data == "": return

        information = json.loads(data[1:])

        match data[0]:
            case "p":
                playerData.clear()
                playerData += information
            case "s":
                for k in serverData.keys(): del serverData[k]
                for k, v in information.items(): serverData[k] = v
        

playerData = []
serverData = {}
client = Client(ip, port, f"Player_{random.randint(0, 1000)}")

tHandleServer = Thread(target=handleServer, args=[client, playerData, serverData])
tDisplay = Thread(target=display.render, args=[client, playerData, serverData])

tHandleServer.start()
tDisplay.start()

tHandleServer.join()
tDisplay.join()

