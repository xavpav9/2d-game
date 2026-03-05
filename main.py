import json, display, random
from client import Client
from threading import Thread
from time import sleep

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
            case "d":
                print("The server has terminated your connection.")
                print("Reasons: ")
                for reason in information: print(f"- {reason}")
                clientData["running"] = False
                return
            case _:
                print(f"unknown request \"{data[0]}\" from server")

playerData = []
serverData = {}
clientData = {"inMenu": True, "running": True}
client = Client(ip, port, f"Player_{str(random.randint(0, 999)).zfill(3)}")

tDisplay = Thread(target=display.render, args=[client, playerData, serverData, clientData])
tHandleServer = Thread(target=handleServer, args=[client, playerData, serverData])

tDisplay.start()

while True:
    if not clientData["running"]:
        break
    elif not clientData["inMenu"]:
        client.initialiseSock()
        tHandleServer.start()
        break
    else:
        sleep(0.5)

try:
    tDisplay.join()
    tHandleServer.join()
except:
    print("bye")
