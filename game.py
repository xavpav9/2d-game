import random, json, time

"""
TODO
    - Red nametag if tagger and blue if not.
    - Allow player to pick their colour or automate based off of role ( or automate nametag based off of role ).
    - I think that I will make this a tag sort of game. Shoot out tag blasts using the mouse, or in the direction of travel using the space bar/RB on controller. Will have to preconfigure.
    - Add player icons perhaps, instead of solid colours.
    - Add arrow key and controller support.
"""

class Game:
    def __init__(self, playerData, serverData):
        self.playerData = playerData
        self.serverData = serverData

    def addServer(self, server):
        self.server = server

    def addPlayer(self, player):
        valid = False
        playerWidth, playerHeight = self.serverData["player"]["defaultSize"]
        while not valid:
            valid = True
            position = [random.randint(0, self.serverData["map"][0] - playerWidth), random.randint(0, self.serverData["map"][1] - playerHeight)]
            for otherPlayer in self.playerData + self.serverData["features"]:
                otherPlayerWidth, otherPlayerHeight = otherPlayer["size"]
                minimumXGap = (playerWidth + otherPlayerWidth) / 2
                minimumYGap = (playerHeight + otherPlayerHeight) / 2
                playerX = position[0] + playerWidth / 2
                playerY = position[1] + playerHeight / 2
                otherPlayerX = otherPlayer["position"][0] + otherPlayerWidth / 2
                otherPlayerY = otherPlayer["position"][1] + otherPlayerHeight / 2

                if abs(playerX - otherPlayerX) < minimumXGap and abs(playerY - otherPlayerY) < minimumYGap:
                    valid = False
                    break

        username = player["username"]
        colour = (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))

        tagger = False
        if len(self.playerData) == 0:
            tagger = True
            self.server.distributeData("a" + json.dumps([f"{username} is the new tagger."]), [])
        else:
            for otherPlayer in self.playerData:
                if otherPlayer["tagger"]:
                    currentTagger = otherPlayer
                    break

            self.server.sendData(player["conn"], "a" + json.dumps([f"{currentTagger['username']} is the tagger."]))

        self.playerData.append({"username": username, "position": position, "colour": colour, "velocity": [0, 0], "size": [playerWidth, playerHeight], "collides": True, "hidden": False, "tagger": tagger})
    
    def removePlayer(self, index):
        replace = False
        if self.playerData[index]["tagger"] and len(self.playerData) > 1: replace = True
        self.playerData.pop(index)

        if replace:
            newTagger = self.playerData[random.randint(0, len(self.playerData) -1)]
            newTagger["tagger"] = True

            self.server.distributeData("a" + json.dumps([f"{newTagger['username']} is the new tagger."]), [])
        

    def handleData(self, data, player):
        """
            v = velocity change
            s = tagger shoots
        """

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
                case "s":
                    shootingAngle = json.loads(data)[0]
                    print(shootingAngle)

        except Exception as e:
            print(e)
            print(f"Invalid data \"{data}\" sent by {player['username']}")

    def fixCollisions(self, player, otherPlayers, dx, dy, collides=True):
        playerWidth, playerHeight = player["size"]
        hidden = False
        for otherPlayer in otherPlayers:
            if otherPlayer != player:
                otherPlayerWidth, otherPlayerHeight = otherPlayer["size"]
                minimumXGap = (playerWidth + otherPlayerWidth) / 2
                minimumYGap = (playerHeight + otherPlayerHeight) / 2
                playerX = player["position"][0] + playerWidth / 2
                playerY = player["position"][1] + playerHeight / 2
                otherPlayerX = otherPlayer["position"][0] + otherPlayerWidth / 2
                otherPlayerY = otherPlayer["position"][1] + otherPlayerHeight / 2

                if abs(playerX - otherPlayerX) < minimumXGap and abs(playerY - otherPlayerY) < minimumYGap:
                    if otherPlayer["collides"]:
                        if dx != 0 and not(abs(playerX - dx - otherPlayerX) + 1 < minimumXGap):
                            player["position"][0] += (minimumXGap - abs(playerX - otherPlayerX)) * (-dx / abs(dx))
                        elif dy != 0 and not(abs(playerY - dy - otherPlayerY) + 1 < minimumYGap):
                            player["position"][1] += (minimumYGap - abs(playerY - otherPlayerY)) * (-dy / abs(dy))
                        else:
                            if dx != 0: player["position"][0] += (minimumXGap - abs(playerX - otherPlayerX)) * (-dx / abs(dx))
                            if dy != 0: player["position"][1] += (minimumYGap - abs(playerY - otherPlayerY)) * (-dy / abs(dy))
                    else:
                        # Hides username if you are behind a non-collidable object.
                        if otherPlayerY + otherPlayerHeight / 2 > playerY + playerHeight / 2: # otherPlayerY is from the centre, so add half of the height to get the bottom.
                            hidden = True
                            if not collides: return True # if the player cannot collide, then this function was just run to see if they where hidden, so it can be exited.

        return hidden


    def tick(self, running):
        tickRate = 30
        frameTime = 1000 / tickRate
        speed = 8

        while running[0]:
            startTime = time.time()
            mapSize = self.serverData["map"]
            
            for player in self.playerData:
                # Move player based on their velocity.
                playerWidth, playerHeight = player["size"]
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
                elif player["position"][0] > mapSize[0] - playerWidth: player["position"][0] = mapSize[0] - playerWidth

                if player["position"][1] < 0: player["position"][1] = 0
                elif player["position"][1] > mapSize[1] - playerHeight: player["position"][1] = mapSize[1] - playerHeight

                if player["collides"]:
                    # Handle other player collisions.
                    hidden = self.fixCollisions(player, self.playerData, dx, dy)

                    # Handle feature collisions.
                    hidden = self.fixCollisions(player, self.serverData["features"], dx, dy) or hidden
                else:
                    hidden = self.fixCollisions(player, self.serverData["features"], dx, dy)

                player["hidden"] = hidden


            self.server.distributeData("p" + json.dumps(self.playerData), [])
            endTime = time.time()
            totalTime = (endTime-startTime)
            if totalTime < frameTime:
                time.sleep((frameTime - totalTime) / 1000)
