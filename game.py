import random, json, time, math

TICKRATE = 30

"""
TODO

n. = priority
1.
    - Normalise timing - either seconds or game ticks, not either
    - I think that I will make this a tag sort of game. Shoot out tag blasts using the mouse, or in the direction of travel using the space bar/RB on controller. Might have to preconfigure controller.
    - Add controller support.
    - New abilities - Larger shot for tagger; See through bushes for all;
2.
    - Add sound effects.
    - Add more assets.
    - Allow user setting up the server to customise a few variables - e.g. how many taggers there are.
3.
    - Maybe add animations for clicking buttons.
    - Add a block that can only be collided with at the base.
"""

class Game:
    def __init__(self, playerData, serverData):
        self.playerData = playerData
        self.serverData = serverData
        self.tickRate = 30
        self.mapTypes = ["Nature Map", "Bushy Map", "Rocky Map"]

    def addServer(self, server):
        self.server = server

    def placePlayer(self, playerSize):
        colliding = True
        playerWidth, playerHeight = playerSize
        while colliding:
            valid = True
            position = [random.randint(0, self.serverData["map"]["size"][0] - playerWidth), random.randint(0, self.serverData["map"]["size"][1] - playerHeight)]
            playerObject = {"position": position, "size": playerSize}

            colliding = False # for when there are no players or features
            for otherPlayer in self.playerData + self.serverData["features"]:
                if otherPlayer["collides"]: colliding = self.checkCollisions(playerObject, otherPlayer)
                if colliding: break

        return position

    def addPlayer(self, player):
        playerSize = self.serverData["player"]["defaultSize"]
        playerWidth, playerHeight = playerSize

        position = self.placePlayer(playerSize)

        username = player["username"]
        colour = (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))

        tagger = False
        if self.serverData["inGame"]:
            if len(self.playerData) == 0:
                tagger = True
                self.server.distributeData("a" + json.dumps({"text": f"{username} is the new tagger.", "size": "big", "colour": (255,0,0)}), [])
            else:
                for otherPlayer in self.playerData:
                    if otherPlayer["tagger"]:
                        currentTagger = otherPlayer
                        break

                self.server.sendData(player["conn"], "a" + json.dumps({"text": f"{currentTagger['username']} is the tagger.", "size": "big", "colour": (255,0,0)}))

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
                                "collectibles": [],
                                "type": "player"})
    
    def removePlayer(self, index):
        replace = False
        if self.playerData[index]["tagger"] and len(self.playerData) > 1: replace = True
        self.playerData.pop(index)

        if replace:
            newTagger = self.playerData[random.randint(0, len(self.playerData) -1)]
            newTagger["tagger"] = True

            self.server.distributeData("a" + json.dumps({"text": f"{newTagger['username']} is the new tagger.", "size": "big", "colour": (255,0,0)}), [])
        

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

                        multiplier = 1

                        for collectible in player["collectibles"]:
                            if collectible["name"] == "largerShot":
                                multiplier *= collectible["multiplier"]

                        size = [dimension * 1.1 * multiplier for dimension in self.serverData["player"]["defaultSize"]]

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
                            if otherPlayer["type"] != "zone": hidden = True # Hides username if you are behind a non-collidable, non-collectible object, unless if it is a zone.

        return hidden, collected

    def setUpMap(self, voting=True):
        currentMap = 0

        if voting:
            zones = []
            for feature in self.serverData["features"]:
                if feature["type"] == "zone":
                    zones.append([feature, 0])

            for player in self.playerData:
                for zone in zones:
                    if self.checkCollisions(player, zone[0]):
                        zone[1] += 1

            highestVotes = -1
            currentZone = 0

            for zone in zones:
                if zone[1] > highestVotes:
                    highestVotes = zone[1]
                    currentZone = zone[0]

            currentMap = self.mapTypes.index(currentZone["name"])

        match currentMap:
            case 0:
                features = []
                mapSize = [random.randint(10, 15) * 100, random.randint(10, 15) * 100]
                maxFeatureHeight = 200
                speedUpWidth = 40
                speedUpHeight = 40
                for i in range(2, (mapSize[1] - maxFeatureHeight) // 100 + 1):
                    rockWidth = random.randint(20, 40)
                    rockHeight = rockWidth + random.randint(-2, 2)
                    bushWidth = random.randint(80, 160)
                    bushHeight = bushWidth // 2 + random.randint(-2, 2)

                    features.append({"name": "rock",
                                     "position": [random.randint(0, mapSize[0] - rockWidth), i * 100 + random.randint(-80, 80)],
                                     "size": [rockWidth, rockHeight],
                                     "collides": True,
                                     "type": "object"})

                    features.append({"name": "bush",
                                     "position": [random.randint(0, mapSize[0] - bushWidth), i * 100 + random.randint(-80, 80)],
                                     "size": [bushWidth, bushHeight],
                                     "collides": False,
                                     "type": "object"})

                    if random.randint(1, 5) == 1:
                        features.append({"name": "speedUp",
                                         "position": [random.randint(0, mapSize[0] - speedUpWidth), i * 100 + random.randint(-80, 80)],
                                         "size": [speedUpWidth, speedUpHeight],
                                         "collides": False,
                                         "type": "collectible",
                                         "time": TICKRATE * 3,
                                         "tagger": True,
                                         "runner": True,
                                         "multiplier": 1.5})

                self.serverData["map"] = {"size": mapSize, "innerColour": (200,255,200), "outerColour": (80,80,255), "name": self.mapTypes[currentMap]}
                self.serverData["features"] = features
            
            case 1:
                features = []
                mapSize = [300, 300]

                for i in range(20):
                    bushWidth = random.randint(100, 120)
                    bushHeight = bushWidth // 2 + random.randint(-2, 2)
                    features.append({"name": "bush",
                                     "position": [random.randint(2, mapSize[0] - bushWidth - 2), random.randint(2, mapSize[1] - bushHeight - 2)],
                                     "size": [bushWidth, bushHeight],
                                     "collides": False,
                                     "type": "object"})

                self.serverData["map"] = {"size": mapSize, "innerColour": (100,255,100), "outerColour": (80,80,255), "name": self.mapTypes[currentMap]}
                self.serverData["features"] = features

            case 2:

                features = []
                mapSize = [700, 700]

                for i in range(60):
                    rockWidth = random.randint(30, 35)
                    rockHeight = rockWidth + random.randint(-2, 2)

                    features.append({"name": "rock",
                                     "position": [random.randint(0, mapSize[0] - rockWidth), random.randint(2, mapSize[1] - rockHeight - 2)],
                                     "size": [rockWidth, rockHeight],
                                     "collides": True,
                                     "type": "object"})

                self.serverData["map"] = {"size": mapSize, "innerColour": (200,200,200), "outerColour": (80,80,255), "name": self.mapTypes[currentMap]}
                self.serverData["features"] = features

                

    def setUpLobby(self):
        mapSize = [400, 400]
        numOfMaps = len(self.mapTypes)
        features = []

        height = mapSize[1] / numOfMaps
        for i in range(numOfMaps):
            startY = int(i / numOfMaps * mapSize[1])
            features.append({"name": f"{self.mapTypes[i]}",
                             "colour": (100 / numOfMaps * i + 155, 100 / numOfMaps * i + 155, 255),
                             "position": [0, startY],
                             "size": [mapSize[0], height],
                             "collides": False,
                             "type": "zone"})


        self.serverData["map"] = {"size": mapSize, "innerColour": (255,255,255), "outerColour": (100, 100, 100), "name": "Lobby"}
        self.serverData["features"] = features


    def tick(self, running):
        tickRate = self.tickRate # ticks per second
        frameTime = 1000 / tickRate # milliseconds per frame
        speed = 8 # x and y speed of player
        timeAborted = 0 # time since last aborted game - for alerts
        maxIntermissionTime = 15 # maximum time for intermissions
        maxGameTime = 90 # maximum game time
        self.serverData["inGame"] = False
        self.serverData["intermissionTime"] = maxIntermissionTime

        while running[0]:
            startTime = time.time()
            if len(self.playerData) != 0:
                if len(self.playerData) == 1 and self.serverData["inGame"]:
                    # Abort game since there is only one person
                    timeAborted = time.time()
                    self.server.distributeData("a" + json.dumps({"text": "Game Aborted", "size": "veryBig", "colour": (255,0,0)}), [])
                    self.serverData["inGame"] = False
                    self.setUpLobby()
                    self.serverData["intermissionTime"] = maxIntermissionTime
                    for player in self.playerData:
                        player["position"] = self.placePlayer(player["size"])
                        player["tagger"] = False

                elif len(self.playerData) == 1:
                    self.serverData["intermissionTime"] = maxIntermissionTime
                    if time.time() - timeAborted > 1: self.server.distributeData("a" + json.dumps({"text": "Waiting for players...", "size": "big", "colour": (0,0,0)}), [])
                elif not self.serverData["inGame"] and len(self.playerData) > 1:
                    # In intermission
                    self.serverData["intermissionTime"] -= 1 / TICKRATE

                    # Countdown to start game
                    if 3 < self.serverData["intermissionTime"] < 3.1:
                        self.server.distributeData("a" + json.dumps({"text": "3", "size": "veryBig", "colour": (255,0,0)}), [])
                    elif 2 < self.serverData["intermissionTime"] < 2.1:
                        self.server.distributeData("a" + json.dumps({"text": "2", "size": "veryBig", "colour": (255,255,0)}), [])
                    elif 1 < self.serverData["intermissionTime"] < 1.1:
                        self.server.distributeData("a" + json.dumps({"text": "1", "size": "veryBig", "colour": (0,255,0)}), [])

                    if self.serverData["intermissionTime"] <= 0:
                        # Game starting
                        self.serverData["inGame"] = True
                        self.serverData["gameTime"] = maxGameTime
                        self.setUpMap()

                        for player in self.playerData: player["position"] = self.placePlayer(player["size"])

                        newTagger = self.playerData[random.randint(0, len(self.playerData) - 1)]
                        newTagger["tagger"] = True

                        self.server.distributeData("a" + json.dumps({"text": f"{newTagger['username']} is the new tagger.", "size": "big", "colour": (255,0,0)}), [])

                elif self.serverData["gameTime"] <= 0:
                    # Game ended
                    self.serverData["inGame"] = False
                    self.serverData["intermissionTime"] = maxIntermissionTime
                    self.setUpLobby()

                    for player in self.playerData:
                        player["position"] = self.placePlayer(player["size"])
                        if player["tagger"]:
                            self.server.distributeData("a" + json.dumps({"text": f"{player['username']} lost.", "size": "big", "colour": (255,0,0)}), [])
                            player["tagger"] = False

                mapSize = self.serverData["map"]["size"]
                
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

                        removed = 0
                        for i in range(len(collectibles)):
                            collectibleIndex = collectibles[i] - removed # -removed to keep it in the correct place in the list
                            collectible = self.serverData["features"][collectibleIndex]
                            if player["tagger"] and collectible["tagger"] or not player["tagger"] and collectible["runner"]: # Only collect it if allowed
                                player["collectibles"].append(collectible)
                                self.serverData["features"].pop(collectibleIndex)
                                removed += 1


                    
                    # Only apply if game is running.
                    if self.serverData["inGame"]:
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

                                        i = 0
                                        while i < len(player["collectibles"]):
                                            if player["collectibles"][i]["tagger"] == False:
                                                player["collectibles"].pop(i)
                                            else:
                                                i += 1

                                        i = 0
                                        while i < len(otherPlayer["collectibles"]):
                                            if otherPlayer["collectibles"][i]["runner"] == False:
                                                otherPlayer["collectibles"].pop(i)
                                            else:
                                                i += 1


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
                            
                        # Countdown to end game
                        if 3 < self.serverData["gameTime"] < 3.1:
                            self.server.distributeData("a" + json.dumps({"text": "3", "size": "veryBig", "colour": (255,0,0)}), [])
                        elif 2 < self.serverData["gameTime"] < 2.1:
                            self.server.distributeData("a" + json.dumps({"text": "2", "size": "veryBig", "colour": (255,255,0)}), [])
                        elif 1 < self.serverData["gameTime"] < 1.1:
                            self.server.distributeData("a" + json.dumps({"text": "1", "size": "veryBig", "colour": (0,255,0)}), [])

                # Only apply if game is running.
                if self.serverData["inGame"]:
                    # Generate a speedUp collectible
                    if random.randint(0, TICKRATE * 10) == 0: 
                        self.serverData["features"].append({"name": "speedUp",
                                        "position": [random.randint(0, mapSize[0] - 40), random.randint(50, mapSize[1] - 50)],
                                         "size": [40, 40],
                                         "collides": False,
                                         "type": "collectible",
                                         "time": TICKRATE * 3,
                                         "tagger": True,
                                         "runner": True,
                                         "multiplier": random.randint(11, 14) / 10})

                    # Generate a larger shot collectible
                    if random.randint(0, TICKRATE * 12) == 0: 
                        self.serverData["features"].append({"name": "largerShot",
                                        "position": [random.randint(0, mapSize[0] - 40), random.randint(50, mapSize[1] - 50)],
                                         "size": [40, 40],
                                         "collides": False,
                                         "type": "collectible",
                                         "time": TICKRATE * 4,
                                         "tagger": True,
                                         "runner": False,
                                         "multiplier": random.randint(11, 14) / 10})

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
                self.server.distributeData("s" + json.dumps(self.serverData), [])

                self.serverData["gameTime"] -= 1 / TICKRATE
            else:
                self.serverData["intermissionTime"] = maxIntermissionTime
                self.serverData["inGame"] = False

            endTime = time.time()
            totalTime = (endTime-startTime) * 1000
            if totalTime < frameTime:
                time.sleep((frameTime - totalTime) / 1000)
