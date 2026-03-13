import random, json, time, math

TICKRATE = 30

"""
TODO
    - Show a display of what collectibles the user has on the side of the screen.
    - Add different maps.
    - I think that I will make this a tag sort of game. Shoot out tag blasts using the mouse, or in the direction of travel using the space bar/RB on controller. Might have to preconfigure controller.
    - Add controller support.
    - Maybe add animations for clicking buttons.
    - Add sound effects.
    - Allow user setting up server to customise a few variables - e.g. how many taggers there are.
    - Perhaps add a lobby to vote on what will happen in the next round.
"""

class Game:
    def __init__(self, playerData, serverData):
        self.playerData = playerData
        self.serverData = serverData
        self.tickRate = 30

    def addServer(self, server):
        self.server = server

    def addPlayer(self, player):
        colliding = True
        playerSize = self.serverData["player"]["defaultSize"]
        playerWidth, playerHeight = playerSize
        while colliding:
            valid = True
            position = [random.randint(0, self.serverData["map"][0] - playerWidth), random.randint(0, self.serverData["map"][1] - playerHeight)]
            playerObject = {"position": position, "size": playerSize}

            for otherPlayer in self.playerData + self.serverData["features"]:
                colliding = self.checkCollisions(playerObject, otherPlayer)
                if colliding: break

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

        self.playerData.append({"username": username,
                                "position": position,
                                "colour": colour,
                                "velocity": [0, 0],
                                "size": [playerWidth, playerHeight],
                                "collides": True,
                                "hidden": False,
                                "tagger": tagger,
                                "cooldown": 0,
                                "shots": [],
                                "iconNumber": 0,
                                "collectibles": []})
    
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
            c = character change
        """

        try:
            for otherPlayer in self.playerData:
                if otherPlayer["username"] == player["username"]:
                    player = otherPlayer
                    break

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
                    if player["cooldown"] <= 0 and player["tagger"]:
                        player["cooldown"] = self.tickRate
                        shootingAngle = json.loads(data)[0]
                        size = [dimension * 1.1 for dimension in self.serverData["player"]["defaultSize"]]
                        player["shots"].append({"size": size,
                                                "angle": shootingAngle,
                                                "time": self.tickRate / 7})
                case "c":
                    player["iconNumber"] = json.loads(data)[0]


        except Exception as e:
            print(e)
            print(f"Invalid data \"{data}\" sent by {player['username']}")

    def checkCollisions(self, player, otherPlayer):
        playerWidth, playerHeight = player["size"]
        otherPlayerWidth, otherPlayerHeight = otherPlayer["size"]
        minimumXGap = (playerWidth + otherPlayerWidth) / 2
        minimumYGap = (playerHeight + otherPlayerHeight) / 2
        playerX = player["position"][0] + playerWidth / 2
        playerY = player["position"][1] + playerHeight / 2
        otherPlayerX = otherPlayer["position"][0] + otherPlayerWidth / 2
        otherPlayerY = otherPlayer["position"][1] + otherPlayerHeight / 2
        return abs(playerX - otherPlayerX) < minimumXGap and abs(playerY - otherPlayerY) < minimumYGap

    def fixCollisions(self, player, otherPlayers, dx, dy, collides=True):
        playerWidth, playerHeight = player["size"]
        collected = []
        hidden = False
        for i in range(len(otherPlayers)):
            otherPlayer = otherPlayers[i]
            if otherPlayer != player:
                otherPlayerWidth, otherPlayerHeight = otherPlayer["size"]
                minimumXGap = (playerWidth + otherPlayerWidth) / 2
                minimumYGap = (playerHeight + otherPlayerHeight) / 2
                playerX = player["position"][0] + playerWidth / 2
                playerY = player["position"][1] + playerHeight / 2
                otherPlayerX = otherPlayer["position"][0] + otherPlayerWidth / 2
                otherPlayerY = otherPlayer["position"][1] + otherPlayerHeight / 2

                if abs(playerX - otherPlayerX) < minimumXGap and abs(playerY - otherPlayerY) < minimumYGap:
                    if otherPlayer["collides"] and player["collides"]:
                        if dx != 0 and not(abs(playerX - dx - otherPlayerX) + 1 < minimumXGap):
                            player["position"][0] += (minimumXGap - abs(playerX - otherPlayerX)) * (-dx / abs(dx))
                        elif dy != 0 and not(abs(playerY - dy - otherPlayerY) + 1 < minimumYGap):
                            player["position"][1] += (minimumYGap - abs(playerY - otherPlayerY)) * (-dy / abs(dy))
                        else:
                            if dx != 0: player["position"][0] += (minimumXGap - abs(playerX - otherPlayerX)) * (-dx / abs(dx))
                            if dy != 0: player["position"][1] += (minimumYGap - abs(playerY - otherPlayerY)) * (-dy / abs(dy))
                    else:
                        if otherPlayer["type"] == "collectible":
                            collected.append(i)
                        elif otherPlayerY + otherPlayerHeight / 2 > playerY + playerHeight / 2: # otherPlayerY and playerY are from the centre, so add half of their heights to get the bottoms.
                            hidden = True # Hides username if you are behind a non-collidable, non-collectible object.
                            #NEED TO REMOVE COMMENT:  if not collides: return True # if the player cannot collide, then this function was just run to see if they were hidden, so it can be exited.


        return hidden, collected


    def tick(self, running):
        tickRate = self.tickRate
        frameTime = 1000 / tickRate
        speed = 8

        while running[0]:
            startTime = time.time()
            mapSize = self.serverData["map"]
            serverDataUpdated = False
            
            for player in self.playerData:
                # Move player based on their velocity.
                playerWidth, playerHeight = player["size"]
                velocity = player["velocity"]

                currentSpeed = speed
                if player["tagger"]: currentSpeed *= 0.95
                for collectible in player["collectibles"]:
                    if collectible["name"] == "speedUp":
                        if player["tagger"]: currentSpeed *= ((collectible["multiplier"])**(1/2))
                        else: currentSpeed *= collectible["multiplier"]

                dx = dy = 0
                if velocity[0] != 0 or velocity[1] != 0:
                    if velocity[0] != 0 and velocity[1] != 0:
                        hypoteneuse = (velocity[0] ** 2 + velocity[1] ** 2) ** (1/2)
                        ratio = currentSpeed / hypoteneuse
                        dx = velocity[0] * ratio
                        dy = velocity[1] * ratio
                    elif velocity[0] != 0:
                        dx = velocity[0] * currentSpeed
                    else:
                        dy = velocity[1] * currentSpeed

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
                        hidden, collectibles = self.fixCollisions(player, self.serverData["features"], dx, dy) or hidden
                    else:
                        hidden, collectibles = self.fixCollisions(player, self.serverData["features"], dx, dy, False)

                    player["hidden"] = hidden

                    for i in range(len(collectibles)):
                        serverDataUpdated = True
                        collectibleIndex = collectibles[i] - i # will remove one item on each loop, so -i to keep it in the correct place
                        player["collectibles"].append(self.serverData["features"][collectibleIndex]) # These will be items or powerups ( which will have a inbuilt timer
                        self.serverData["features"].pop(collectibleIndex)


                
                # Check if they have been hit.
                for otherPlayer in self.playerData:
                    if otherPlayer["username"] != player["username"]:
                        for shot in otherPlayer["shots"]:
                            # {"username", "playerSize", "position", "angle", "time", "size"}
                            quadrant = abs((shot["angle"] + math.pi / 8) % (2 * math.pi)) // (math.pi / 4)
                            position = [otherPlayer["position"][0] + otherPlayer["size"][0] / 2, otherPlayer["position"][1] + otherPlayer["size"][1] / 2]
                            # position is currently at the centre of the otherPlayer, pointing down right
                            match quadrant:
                                case 0: # above otherPlayer
                                    position[0] -= shot["size"][0] / 2
                                    position[1] -= shot["size"][1]
                                case 1: # top right
                                    position[1] -= shot["size"][1]
                                case 2: # right
                                    position[1] -= shot["size"][1] / 2
                                # case 3: bottom right, already in correct position
                                case 4: # bottom
                                    position[0] -= shot["size"][0] / 2
                                case 5: # bottom left
                                    position[0] -= shot["size"][0]
                                case 6: # left
                                    position[0] -= shot["size"][0]
                                    position[1] -= shot["size"][1] / 2
                                case 7: # top left
                                    position[0] -= shot["size"][0]
                                    position[1] -= shot["size"][1]
                                    
                            shotObject = {"position": position, "size": shot["size"]}
                            colliding = self.checkCollisions(player, shotObject)

                            if colliding and not player["tagger"]:
                                otherPlayer["tagger"] = False
                                otherPlayer["cooldown"] = 0
                                player["tagger"] = True
                                if shot["time"] >= 2: shot["time"] = 2

                if player["cooldown"] > 0: player["cooldown"] -= 1
                else: player["cooldown"] = 0

                i = 0
                while i < len(player["collectibles"]):
                    collectible = player["collectibles"][i]
                    if collectible["time"] > 0:
                        collectible["time"] -= 1
                        if collectible["time"] <= 0:
                            player["collectibles"].pop(i)
                            i -= 1
                    i += 1

            # Reduce existence time for shot
            for player in self.playerData:
                i = 0
                while i < len(player["shots"]):
                    shot = player["shots"][i]
                    shot["time"] -= 1
                    if shot["time"] <= 0:
                        player["shots"].pop(i)
                    else: i += 1

            self.server.distributeData("p" + json.dumps(self.playerData), [])

            if serverDataUpdated: self.server.distributeData("s" + json.dumps(self.serverData), [])
            endTime = time.time()
            totalTime = (endTime-startTime)
            if totalTime < frameTime:
                time.sleep((frameTime - totalTime) / 1000)
