from client import Client
import json
from threading import Thread

ip = "127.0.0.1"
port = 2000

def handleServer(client, player_data, server_data):
    while True:
        data = client.recvData()
        if data == "": return

        information = json.loads(data[1:])

        match data[0]:
            case "p":
                player_data.clear()
                player_data += information
                print("updated player data")
            case "s":
                server_data.clear()
                server_data += information
                print("updated server data")
        

player_data = []
server_data = []
client = Client(ip, port, "Player_1")

tHandleServer = Thread(target=handleServer, args=[client, player_data, server_data])

tHandleServer.start()
tHandleServer.join()

