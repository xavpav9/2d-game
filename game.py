class Game:
    def __init__(self, playerData, serverData):
        self.playerData = playerData
        self.serverData = serverData

    def addPlayer(self, player):
        self.playerData.append({"username": player["username"]})

    def removePlayer(self, index):
        self.playerData.pop(index)

    def handleData(self, data, player):
        pass
