import random

class Game:
    def __init__(self, playerData, serverData):
        self.playerData = playerData
        self.serverData = serverData

    def addPlayer(self, player):
        position = [random.randint(0, 100), random.randint(0, 100)]
        username = player["username"]
        colour = (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))
        self.playerData.append({"username": username, "position": position, "colour": colour})

    def removePlayer(self, index):
        self.playerData.pop(index)

    def handleData(self, data, player):
        pass
