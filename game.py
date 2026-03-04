import random, json, time

class Game:
    def __init__(self, playerData, serverData):
        self.playerData = playerData
        self.serverData = serverData

    def addPlayer(self, player):
        position = [random.randint(0, 100), random.randint(0, 100)]
        username = player["username"]
        colour = (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))
        self.playerData.append({"username": username, "position": position, "colour": colour, "velocity": [0, 0]})

    def removePlayer(self, index):
        self.playerData.pop(index)

    def handleData(self, data, player):
        try:
            dataType = data[0]
            data = data[1:]
            username = player["username"]

            match dataType:
                case "v":
                    newVelocity = json.loads(data)
                    if newVelocity[0] != 0: newVelocity[0] = newVelocity[0] / abs(newVelocity[0])
                    if newVelocity[1] != 0: newVelocity[1] = newVelocity[1] / abs(newVelocity[1])

                    for otherPlayer in self.playerData:
                        if otherPlayer["username"] == username:
                            otherPlayer["velocity"] = newVelocity
        except Exception as e:
            print(e)
            print(f"Invalid data \"{data}\" sent by {player['username']}")

    def tick(self, server, running):
        tickRate = 30
        frameTime = 1000 / tickRate
        speed = 8

        while running[0]:
            startTime = time.time()
            mapSize = self.serverData["map"]
            playerSize = self.serverData["player"]["size"]
            
            for player in self.playerData:
                velocity = player["velocity"]
                if velocity[0] == velocity[1] == 0:
                    continue
                elif velocity[0] != 0 and velocity[1] != 0:
                    hypoteneuse = (velocity[0] ** 2 + velocity[1] ** 2) ** (1/2)
                    ratio = speed / hypoteneuse
                    player["position"][0] += velocity[0] * ratio
                    player["position"][1] += velocity[1] * ratio
                elif velocity[0] != 0:
                    player["position"][0] += velocity[0] * speed
                else:
                    player["position"][1] += velocity[1] * speed

                if player["position"][0] < 0: player["position"][0] = 0
                elif player["position"][0] > mapSize[0] - playerSize: player["position"][0] = mapSize[0] - playerSize

                if player["position"][1] < 0: player["position"][1] = 0
                elif player["position"][1] > mapSize[1] - playerSize: player["position"][1] = mapSize[1] - playerSize

            server.distributeData("p" + json.dumps(self.playerData), [])

            endTime = time.time()
            totalTime = (endTime-startTime)
            if totalTime < frameTime:
                time.sleep((frameTime - totalTime) / 1000)



