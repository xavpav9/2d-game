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
                return
            case _:
                print(f"unknown request \"{data[0]}\" from server")

playerData = []
serverData = {}
inMenu = [True]
# client = Client(ip, port, f"Player_{random.randint(0, 1000)}")
username = input("username: ")
client = Client(ip, port, username)

tDisplay = Thread(target=display.render, args=[client, playerData, serverData, inMenu])
tHandleServer = Thread(target=handleServer, args=[client, playerData, serverData])

tDisplay.start()

while True:
    if not inMenu[0]:
        client.initialiseSock()
        tHandleServer.start()
        break
    else:
        sleep(0.5)

tDisplay.join()
tHandleServer.join()
