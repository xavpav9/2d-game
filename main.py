import json, display, random
from client import Client
from threading import Thread
from time import sleep

ip = "127.0.0.1"
port = 2000

def handleServer(client, playerData, serverData, clientData):
    while True:
        data = client.recvData()
        if data == "":
            clientData["problem"] = "Disconnected from server."
            return

        information = json.loads(data[1:])

        match data[0]:
            case "p":
                playerData.clear()
                playerData += information
            case "s":
                serverData.clear()
                for k, v in information.items(): serverData[k] = v
            case "d":
                print("The server has terminated your connection.")
                print("Reasons: ")
                for reason in information: print(f"- {reason}")
                clientData["problem"] = " ".join(information)
                return 
            case "a":
                clientData["alert"] = information[0]
            case _:
                print(f"unknown request \"{data[0]}\" from server")

playerData = []
serverData = {}
clientData = {"inMenu": True, "running": True, "problem": "", "alert": ""}
client = Client(ip, port, f"Player_{str(random.randint(0, 999)).zfill(3)}")

renderer = display.Renderer(client, playerData, serverData, clientData)
tDisplay = Thread(target=renderer.render, args=[])
tDisplay.start()

while True:
    tHandleServer = Thread(target=handleServer, args=[client, playerData, serverData, clientData])
    while True:
        if not clientData["running"]:
            break
        elif not clientData["inMenu"]:
            success = client.initialiseSock()
            client.sendData("c" + json.dumps([clientData["iconNumber"]]))
            if success == True:
                tHandleServer.start()
                break
            else:
                clientData["inMenu"] = True
                clientData["problem"] = "Failed to connect to server"
        else:
            sleep(0.2)

    if not clientData["running"]: break

    tHandleServer.join()
    clientData["inMenu"] = True

try:
    tDisplay.join()
except:
    pass

print("bye")
