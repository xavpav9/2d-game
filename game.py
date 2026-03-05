import random, json, time

"""
TODO
    - Add more different object features (i.e a bush).
    - Allow player to pick their colour.
    - I think that I will make this a tag sort of game. Shoot out tag blasts using the mouse, or in the direction of travel using the space bar/RB on controller. Will have to preconfigure.
    - Add player icons perhaps, instead of solid colours.
    - Add arrow key and controller support.
    - Allow different rectangular sized hitboxes by changing the "size" variable in the players/features to hold a width and height instead.
"""

class Game:
    def __init__(self, playerData, serverData):
        self.playerData = playerData
        self.serverData = serverData

    def addPlayer(self, player):
        valid = False
        playerSize = self.serverData["player"]["defaultSize"]
        while not valid:
            valid = True
            position = [random.randint(0, self.serverData["map"][0] - playerSize), random.randint(0, self.serverData["map"][1] - playerSize)]
            for otherPlayer in self.playerData + self.serverData["features"]:
                otherPlayerSize = otherPlayer["size"]
                minimumGap = (playerSize + otherPlayerSize) / 2
                playerX = position[0] + playerSize / 2
                playerY = position[1] + playerSize / 2
                otherPlayerX = otherPlayer["position"][0] + otherPlayerSize / 2
                otherPlayerY = otherPlayer["position"][1] + otherPlayerSize / 2

                if abs(playerX - otherPlayerX) < minimumGap and abs(playerY - otherPlayerY) < minimumGap:
                    valid = False
                    break

        username = player["username"]
        colour = (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))
        self.playerData.append({"username": username, "position": position, "colour": colour, "velocity": [0, 0], "size": 30, "collides": True, "hidden": False})
    
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

    def fixCollisions(self, player, otherPlayers, dx, dy, collides=True):
        playerSize = player["size"]
        hidden = False
        for otherPlayer in otherPlayers:
            if otherPlayer != player:
                otherPlayerSize = otherPlayer["size"]
                minimumGap = (playerSize + otherPlayerSize) / 2
                playerX = player["position"][0] + playerSize / 2
                playerY = player["position"][1] + playerSize / 2
                otherPlayerX = otherPlayer["position"][0] + otherPlayerSize / 2
                otherPlayerY = otherPlayer["position"][1] + otherPlayerSize / 2

                if abs(playerX - otherPlayerX) < minimumGap and abs(playerY - otherPlayerY) < minimumGap:
                    if otherPlayer["collides"]:
                        if dx != 0 and not(abs(playerX - dx - otherPlayerX) + 1 < minimumGap):
                            player["position"][0] += (minimumGap - abs(playerX - otherPlayerX)) * (-dx / abs(dx))
                        elif dy != 0 and not(abs(playerY - dy - otherPlayerY) + 1 < minimumGap):
                            player["position"][1] += (minimumGap - abs(playerY - otherPlayerY)) * (-dy / abs(dy))
                        else:
                            if dx != 0: player["position"][0] += (minimumGap - abs(playerX - otherPlayerX)) * (-dx / abs(dx))
                            if dy != 0: player["position"][1] += (minimumGap - abs(playerY - otherPlayerY)) * (-dy / abs(dy))
                    else:
                        hidden = True
                        if not collides: return True

        return hidden


    def tick(self, server, running):
        tickRate = 30
        frameTime = 1000 / tickRate
        speed = 8

        while running[0]:
            startTime = time.time()
            mapSize = self.serverData["map"]
            
            for player in self.playerData:
                # Move player based on their velocity.
                playerSize = player["size"]
                velocity = player["velocity"]
                dx = dy = 0
                if velocity[0] == velocity[1] == 0:
                    continue
                elif velocity[0] != 0 and velocity[1] != 0:
                    hypoteneuse = (velocity[0] ** 2 + velocity[1] ** 2) ** (1/2)
                    ratio = speed / hypoteneuse
                    dx = velocity[0] * ratio
                    dy = velocity[1] * ratio
                elif velocity[0] != 0:
                    dx = velocity[0] * speed
                else:
                    dy = velocity[1] * speed

                player["position"][0] += dx
                player["position"][1] += dy
                # Map border collisions.
                if player["position"][0] < 0: player["position"][0] = 0
                elif player["position"][0] > mapSize[0] - playerSize: player["position"][0] = mapSize[0] - playerSize

                if player["position"][1] < 0: player["position"][1] = 0
                elif player["position"][1] > mapSize[1] - playerSize: player["position"][1] = mapSize[1] - playerSize

                if player["collides"]:
                    # Handle other player collisions.
                    hidden = self.fixCollisions(player, self.playerData, dx, dy)

                    # Handle feature collisions.
                    hidden = self.fixCollisions(player, self.serverData["features"], dx, dy) or hidden
                else:
                    hidden = self.fixCollisions(player, self.serverData["features"], dx, dy)

                player["hidden"] = hidden


            server.distributeData("p" + json.dumps(self.playerData), [])

            endTime = time.time()
            totalTime = (endTime-startTime)
            if totalTime < frameTime:
                time.sleep((frameTime - totalTime) / 1000)
