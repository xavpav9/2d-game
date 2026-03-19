import pygame, json, math
from time import sleep

W, H = 800, 600
WHITE, BLACK, RED, GREEN, BLUE = (255,255,255), (0,0,0), (255,0,0), (0,255,0), (0,0,255)
FPS = 30

class Renderer:
    def __init__(self, client, playerData, serverData, clientData):
        self.client = client
        self.playerData = playerData
        self.serverData = serverData
        self.clientData = clientData


        self.velocity = [0, 0] # x and y velocities
        self.clickPos = [0, 0] # position of click so that it is known when user releases mouse click
        self.btnPadding = [20, 10] # x and y padding of buttons on menu screen
        self.uiPadding = [10, 10] # x and y padding for ui on game screen
        self.menuWait = [-1, False] # for bottomText pop ups. index 0: current frame since started, index 2: whether the client is trying to connect to the server or not
        self.alertWait = [-1] # for game alerts. index 0: current frame since started
        self.ctrl = False # whether ctrl is being held
        self.validUsernameCharacters = "abcdefghijklmnopqrstuvwxyz1234567890_- "
        self.featureIcons = {"noTexture": pygame.image.load("res/noTexture.png"), "rock": pygame.image.load("res/features/rock.png"), "bush": pygame.image.load("res/features/bush.png"), "speedUp": pygame.image.load("res/features/speedUp.png")}

        self.characterIcons = [{"icon": "", "name": "Random Colour"}, {"icon": pygame.image.load("res/characters/guard.png"), "name": "Guard"}, {"icon": pygame.image.load("res/characters/rainbow.png"), "name": "Rainbow"}]
        self.clientData["iconNumber"] = 0

        self.leaveBtn = pygame.transform.scale(pygame.image.load("res/buttons/leave.svg"), (30, 40))

    def getPlayerDisplayInfo(self, currentUsername):
        # playerInfo = [x, y, colour, size, hiddenUsername?, iconNumber] size=width,height
        usernamePositions = []
        playerPositions = []

        for player in self.playerData:
            width, height = player["size"]
            xPos, yPos = player["position"]
            shots = player["shots"]
            username = player["username"]
            usernameColour = (0, 0, 255)
            if player["tagger"]: usernameColour = (255, 0, 0)
            renderedUsername = self.font.render(username, True, usernameColour)
            xUsername = xPos + (width / 2) - (renderedUsername.get_size()[0] / 2)
            yUsername = yPos - 10 - renderedUsername.get_size()[1]

            usernameInfo = [xUsername, yUsername, renderedUsername]
            playerInfo = [xPos, yPos, player["colour"], (width, height), player["hidden"], shots, int(player["iconNumber"]), player["tagger"]]

            if currentUsername == username:
                currentPlayerInfo = playerInfo

            usernamePositions.append(usernameInfo)
            playerPositions.append(playerInfo)

        # sorting based off of the y value + playerSize.
        playerPositions, usernamePositions = [list(positions) for positions in zip(*sorted(zip(playerPositions, usernamePositions), key=lambda data: data[0][1] + data[0][3][1]))]

        return playerPositions, usernamePositions, currentPlayerInfo

    def getFeaturesDisplayInfo(self, featuresData):
        # featureInfo = [x, y, size, name] size=width,height
        featurePositions = []
        for feature in featuresData:
            xPos, yPos = feature["position"]
            width, height = feature["size"]
            name = feature["name"]
            featurePositions.append([xPos, yPos, (width, height), name])

        # sorting based off of the y value + playerSize.
        return sorted(featurePositions, key=lambda data: data[1] + data[2][1])


    def displayPlayer(self, playerInfo, usernameInfo, offset):
        # playerInfo = [x, y, colour, size, hiddenUsername, shots, iconNumber, tagger] size=width,height, shots={angle, size}
        playerWidth, playerHeight = playerInfo[3]
        playerX = playerInfo[0] - offset[0] + self.screen.get_size()[0] / 2
        playerY = playerInfo[1] - offset[1] + self.screen.get_size()[1] / 2
        
        # Draw shots
        for shot in playerInfo[5]:
            quadrant = abs((shot["angle"] + math.pi / 8) % (2 * math.pi)) // (math.pi / 4)
            position = [playerX + playerWidth / 2, playerY + playerHeight / 2]
            # position is currently at the centre of the player, pointing down right
            match quadrant:
                case 0: # above player
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

            pygame.draw.rect(self.screen, (255, 0, 0), (position[0], position[1], shot["size"][0], shot["size"][1]))

        if not playerInfo[4]:
            usernameX = usernameInfo[0] - offset[0] + self.screen.get_size()[0] / 2
            usernameY = usernameInfo[1] - offset[1] + self.screen.get_size()[1] / 2
            self.screen.blit(usernameInfo[2], (usernameX, usernameY))

        if 1 <= playerInfo[6] < len(self.characterIcons):
            icon = pygame.transform.scale(self.characterIcons[playerInfo[6]]["icon"], (playerWidth, playerHeight))
            self.screen.blit(icon, (playerX, playerY))
        else:
            pygame.draw.rect(self.screen, playerInfo[2], (playerX, playerY, playerWidth, playerHeight))

        if playerInfo[7]: # blue/red outlines
            pygame.draw.rect(self.screen, RED, (playerX, playerY, playerWidth, playerHeight), 1)
        else:
            pygame.draw.rect(self.screen, BLUE, (playerX, playerY, playerWidth, playerHeight), 1)

    def displayFeature(self, featureInfo, offset):
        # featureInfo = [x, y, size, name] size=width,height
        width, height = featureInfo[2]
        featureX = featureInfo[0] - offset[0] + self.screen.get_size()[0] / 2
        featureY = featureInfo[1] - offset[1] + self.screen.get_size()[1] / 2

        icon = self.featureIcons["noTexture"]
        if featureInfo[3] in self.featureIcons.keys(): icon = self.featureIcons[featureInfo[3]]
        scaledIcon = pygame.transform.scale(icon, (width, height))
        self.screen.blit(scaledIcon, (featureX, featureY))

    def calculateAngle(self, x, y):
        if x == 0:
            if y > 0: angle = 0
            else: angle = math.pi
        elif y == 0:
            if x > 0: angle = math.pi / 2
            else: angle = 3 * math.pi / 2
        else:
            angle = math.atan(abs(y / x))
            if x > 0 and y > 0:
                angle = math.pi / 2 - angle
            elif x > 0 and y < 0:
                angle += math.pi / 2
            elif x < 0 and y < 0:
                angle = 3 * math.pi / 2 - angle
            elif x < 0 and y > 0:
                angle += 3 * math.pi / 2
        return angle

    def getMenuButtonPositions(self):
        # -- Get Display Menu -- #

        width, height = self.screenSize

        # Play button

        playBtnTextXY = (width/2 - self.playBtn.get_size()[0]/2, 3*height/5)
        playBtnXY, playBtnSize = (playBtnTextXY[0] - self.btnPadding[0], playBtnTextXY[1] - self.btnPadding[1]), (self.playBtn.get_size()[0] + self.btnPadding[0] * 2, self.playBtn.get_size()[1] + self.btnPadding[1] * 2)

        # Quit button

        quitBtnTextXY = (width/2 - self.quitBtn.get_size()[0]/2, 7*height/10)
        quitBtnXY, quitBtnSize = (quitBtnTextXY[0] - self.btnPadding[0], quitBtnTextXY[1] - self.btnPadding[1]), (self.quitBtn.get_size()[0] + self.btnPadding[0] * 2, self.quitBtn.get_size()[1] + self.btnPadding[1] * 2)


        # Display character image carousel

        characterText = self.font.render(self.characterIcons[self.clientData["iconNumber"]]["name"], True, BLACK)

        characterLeftArrowXY = (width/2 - self.characterWidth - 10 - self.leftArrow.get_size()[0], 2*height/5 + characterText.get_size()[1])
        characterRightArrowXY = (width/2 + self.characterWidth + 10, 2*height/5 + characterText.get_size()[1])

        return {
                "playBtn": {"position": playBtnXY, "size": playBtnSize},
                "playBtnText": {"position": playBtnTextXY},
                "quitBtn": {"position": quitBtnXY, "size": quitBtnSize},
                "quitBtnText": {"position": quitBtnTextXY},
                "leftArrow": {"position": characterLeftArrowXY, "size": self.leftArrow.get_size()},
                "rightArrow": {"position": characterRightArrowXY, "size": self.rightArrow.get_size()},
                }

    def getGameButtonPositions(self):
        width, height = self.screenSize
        leaveBtnXY, leaveBtnSize = (self.screenSize[0] - self.leaveBtn.get_size()[0] - self.uiPadding[0], self.uiPadding[1]), (self.leaveBtn.get_size()[0], self.leaveBtn.get_size()[1])

        return {
                "leaveBtn": {"position": leaveBtnXY, "size": leaveBtnSize},
                }


    def render(self):

        pygame.init()

        typeface = "freemono"
        availableFonts = pygame.font.get_fonts()
        if typeface not in availableFonts: typeface = availableFonts[0]

        clock = pygame.time.Clock()
        self.bigFont = pygame.font.SysFont(typeface, 40, True, True)
        self.mediumFont = pygame.font.SysFont(typeface, 30, True, True)
        self.font = pygame.font.SysFont(typeface, 20, True, True)
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Game")

        self.title = self.bigFont.render("Tag", True, BLACK)
        self.bottomText = self.font.render("", True, BLACK)
        self.alertText = self.bigFont.render("", True, RED)
        self.playBtn = self.font.render("Play", True, BLACK)
        self.quitBtn = self.font.render("Quit", True, RED)

        self.characterWidth, self.characterHeight = [30, 30]
        leftArrow = pygame.image.load("res/buttons/leftArrow.png")
        rightArrow = pygame.image.load("res/buttons/rightArrow.png")

        leftArrowScaleRatio = self.characterHeight / leftArrow.get_size()[1]
        leftArrowScaleRatio = self.characterHeight / rightArrow.get_size()[1]
        self.leftArrow = pygame.transform.scale(leftArrow, (leftArrow.get_size()[0] * leftArrowScaleRatio, leftArrow.get_size()[1] * leftArrowScaleRatio))
        self.rightArrow = pygame.transform.scale(rightArrow, (rightArrow.get_size()[0] * leftArrowScaleRatio, rightArrow.get_size()[1] * leftArrowScaleRatio))

        while self.clientData["running"]:
            self.screenSize = self.screen.get_size()
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    self.clientData["running"] = False
                elif evt.type == pygame.KEYDOWN:
                    if evt.key == pygame.K_LCTRL:
                        self.ctrl = True
                    elif self.clientData["inMenu"]:
                        if evt.unicode.lower() != "" and evt.unicode.lower() in self.validUsernameCharacters and (self.menuWait[0] == -1 or not self.menuWait[1]):
                            if len(self.client.username) < 15: self.client.username += evt.unicode
                        elif evt.key == pygame.K_BACKSPACE and (self.menuWait[0] == -1 or not self.menuWait[1]):
                            if self.ctrl: self.client.username = ""
                            elif len(self.client.username) > 0: self.client.username = self.client.username[:-1]
                        elif evt.key == pygame.K_RETURN: # Connect to game when <CR> is pressed
                            if len(self.client.username) >= 2:
                                self.clientData["inMenu"] = False
                                self.bottomText = self.font.render("Connecting to server...", True, GREEN)
                                self.menuWait = [FPS/4, True]
                            else:
                                self.bottomText = self.font.render("Username too short", True, RED)
                                self.menuWait = [0, False]
                        elif evt.key == pygame.K_LEFT:
                            self.clientData["iconNumber"] = (self.clientData["iconNumber"] - 1) % len(self.characterIcons)
                        elif evt.key == pygame.K_RIGHT:
                            self.clientData["iconNumber"] = (self.clientData["iconNumber"] + 1) % len(self.characterIcons)
                        elif evt.key == pygame.K_ESCAPE: # Quit game when Esc is pressed in menu
                            self.clientData["running"] = False

                    elif self.menuWait[0] == -1:
                        newData = False
                        if evt.key == pygame.K_a or evt.key == pygame.K_LEFT:
                            newData = True
                            self.velocity[0] = -1
                        elif evt.key == pygame.K_d or evt.key == pygame.K_RIGHT:
                            newData = True
                            self.velocity[0] = 1
                        elif evt.key == pygame.K_w or evt.key == pygame.K_UP:
                            newData = True
                            self.velocity[1] = -1
                        elif evt.key == pygame.K_s or evt.key == pygame.K_DOWN:
                            newData = True
                            self.velocity[1] = 1
                        elif evt.key == pygame.K_ESCAPE: # Return to menu when Esc is pressed in game
                            self.client.close()
                            self.clientData["inMenu"] = True
                            self.bottomText = self.font.render("Disconnected from server.", True, RED)
                            self.menuWait = [0, False]
                        elif evt.key == pygame.K_SPACE:
                            x = self.velocity[0]
                            y = -self.velocity[1]

                            angle = self.calculateAngle(x, y)

                            self.client.sendData("s" + json.dumps([angle]))

                        if newData:
                            self.client.sendData("v" + json.dumps(self.velocity))

                elif evt.type == pygame.KEYUP:
                    if evt.key == pygame.K_LCTRL:
                        self.ctrl = False
                    elif self.clientData["inMenu"]:
                        pass
                    else:
                        newData = False
                        if (evt.key == pygame.K_a or evt.key == pygame.K_LEFT) and self.velocity[0] != 1:
                            newData = True
                            self.velocity[0] = 0
                        elif (evt.key == pygame.K_d or evt.key == pygame.K_RIGHT) and self.velocity[0] != -1:
                            newData = True
                            self.velocity[0] = 0
                        elif (evt.key == pygame.K_w or evt.key == pygame.K_UP) and self.velocity[1] != 1:
                            newData = True
                            self.velocity[1] = 0
                        elif (evt.key == pygame.K_s or evt.key == pygame.K_DOWN) and self.velocity[1] != -1:
                            newData = True
                            self.velocity[1] = 0

                        if newData:
                            self.client.sendData("v" + json.dumps(self.velocity))

                elif evt.type == pygame.MOUSEBUTTONDOWN:
                    self.clickPos = pygame.mouse.get_pos()
                    if not self.clientData["inMenu"]:
                        x = self.clickPos[0] - self.screenSize[0] / 2
                        y = self.screenSize[1] / 2 - self.clickPos[1]
                        angle = self.calculateAngle(x, y)

                        self.client.sendData("s" + json.dumps([angle]))

                elif evt.type == pygame.MOUSEBUTTONUP:
                    if self.clientData["inMenu"]:
                        width, height = self.screenSize
                        buttonPositions = self.getMenuButtonPositions()

                        if 0 < self.clickPos[0] - buttonPositions["playBtn"]["position"][0] < buttonPositions["playBtn"]["size"][0] and 0 < self.clickPos[1] - buttonPositions["playBtn"]["position"][1] < (buttonPositions["playBtn"]["size"][1]):
                            if len(self.client.username) >= 2:
                                self.clientData["inMenu"] = False
                                self.bottomText = self.font.render("Connecting to server...", True, GREEN)
                                self.menuWait = [FPS/4, True]
                            else:
                                self.bottomText = self.font.render("Username too short", True, RED)
                                self.menuWait = [0, False]

                        elif 0 < self.clickPos[0] - buttonPositions["quitBtn"]["position"][0] < buttonPositions["quitBtn"]["size"][0] and 0 < self.clickPos[1] - buttonPositions["quitBtn"]["position"][1] < (buttonPositions["quitBtn"]["size"][1]):
                            self.clientData["running"] = False
                        elif 0 < self.clickPos[0] - buttonPositions["leftArrow"]["position"][0] < buttonPositions["leftArrow"]["size"][0] and 0 < self.clickPos[1] - buttonPositions["leftArrow"]["position"][1] < (buttonPositions["leftArrow"]["size"][1]):
                            self.clientData["iconNumber"] = (self.clientData["iconNumber"] - 1) % len(self.characterIcons)
                        elif 0 < self.clickPos[0] - buttonPositions["rightArrow"]["position"][0] < buttonPositions["rightArrow"]["size"][0] and 0 < self.clickPos[1] - buttonPositions["rightArrow"]["position"][1] < (buttonPositions["rightArrow"]["size"][1]):
                            self.clientData["iconNumber"] = (self.clientData["iconNumber"] + 1) % len(self.characterIcons)


                    else:
                        buttonPositions = self.getGameButtonPositions()

                        if 0 < self.clickPos[0] - buttonPositions["leaveBtn"]["position"][0] < buttonPositions["leaveBtn"]["size"][0] and 0 < self.clickPos[1] - buttonPositions["leaveBtn"]["position"][1] < buttonPositions["leaveBtn"]["size"][0]:
                            self.client.close()
                            self.clientData["inMenu"] = True
                            self.bottomText = self.font.render("Disconnected from server.", True, RED)
                            self.menuWait = [0, False]



            self.screen.fill(WHITE)

            if not self.clientData["running"]: break

            if self.clientData["inMenu"] or self.menuWait[0] != -1:
                # -- Display Menu -- #

                width, height = self.screenSize
                buttonPositions = self.getMenuButtonPositions()

                # Display title button

                titleX, titleY = (width/2 - self.title.get_size()[0]/2, height/6)

                self.screen.blit(self.title, (titleX, titleY))
                pygame.draw.line(self.screen, BLACK, (titleX, titleY+self.title.get_size()[1]), (titleX+self.title.get_size()[0], titleY+self.title.get_size()[1]), 4)

                # Display username

                usernameDisplay = self.font.render(self.client.username, True, BLUE)

                self.screen.blit(usernameDisplay, (width/2 - usernameDisplay.get_size()[0]/2, height/3))

                # Display play button

                self.screen.blit(self.playBtn, buttonPositions["playBtnText"]["position"])
                pygame.draw.rect(self.screen, BLACK, buttonPositions["playBtn"]["position"] + buttonPositions["playBtn"]["size"], 4, 5)

                # Display quit button

                self.screen.blit(self.quitBtn, buttonPositions["quitBtnText"]["position"])
                pygame.draw.rect(self.screen, BLACK, buttonPositions["quitBtn"]["position"] + buttonPositions["quitBtn"]["size"], 4, 5)

                # Display character image carousel

                characterText = self.font.render(self.characterIcons[self.clientData["iconNumber"]]["name"], True, BLACK)
                characterTextX, characterTextY = (width/2 - characterText.get_size()[0]/2, 2*height/5)
                characterImageX, characterImageY = (width/2 - self.characterWidth/2, 2*height/5 + characterText.get_size()[1])

                self.screen.blit(characterText, (characterTextX, characterTextY))
                self.screen.blit(self.leftArrow, buttonPositions["leftArrow"]["position"])
                self.screen.blit(self.rightArrow, buttonPositions["rightArrow"]["position"])

                if self.clientData["iconNumber"] != 0:
                    characterImage = pygame.transform.scale(self.characterIcons[self.clientData["iconNumber"]]["icon"], (self.characterWidth, self.characterHeight))
                    self.screen.blit(characterImage, (characterImageX, characterImageY))
                else:
                    pygame.draw.rect(self.screen, RED, (characterImageX, characterImageY, self.characterWidth, self.characterHeight))



                if self.menuWait[0] != -1:
                    self.screen.blit(self.bottomText, (width/2-self.bottomText.get_size()[0]/2, 4*height/5))
                if self.menuWait[0] >= FPS:
                    self.menuWait[0] = -1
                    if self.menuWait[1]: # when connecting to server == True
                        while len(self.playerData) == 0:
                            sleep(0.1)
                            if self.clientData["inMenu"]:
                                # unsuccessful attempt to connect to server, so main.py has set the "inMenu" flag back to true
                                self.bottomText = self.font.render(self.clientData["problem"], True, RED)
                                self.menuWait = [0, False]
                                break

            else:
                # -- Display Current Game -- #

                for otherPlayer in self.playerData:
                    if otherPlayer["username"] == self.client.username:
                        player = otherPlayer
                        break

                playerPositions, usernamePositions, currentPlayerInfo = self.getPlayerDisplayInfo(self.client.username)
                featurePositions = self.getFeaturesDisplayInfo(self.serverData["features"])
                offset = [currentPlayerInfo[i] + currentPlayerInfo[3][i] / 2 for i in range(2)]

                # Draw Map
                mapSize = self.serverData["map"]["size"]
                borderWidth = 2
                # - Map border
                pygame.draw.rect(self.screen, BLACK, (self.screenSize[0] / 2 - offset[0] - borderWidth, self.screenSize[1] / 2 - offset[1] - borderWidth, mapSize[0] + borderWidth * 2, mapSize[1] + borderWidth * 2), borderWidth)
                # - Map inner
                pygame.draw.rect(self.screen, self.serverData["map"]["innerColour"], (self.screenSize[0]/2 - offset[0], self.screenSize[1]/2 - offset[1], mapSize[0], mapSize[1]))
                # - Map outer
                pygame.draw.rect(self.screen, self.serverData["map"]["outerColour"], (self.screenSize[0]/2 - offset[0] - borderWidth, self.screenSize[1]/2 - offset[1] - borderWidth - 1000, mapSize[0] * 2 + 1000 , 1000)) # top
                pygame.draw.rect(self.screen, self.serverData["map"]["outerColour"], (self.screenSize[0]/2 - offset[0] + mapSize[0] + borderWidth, self.screenSize[1]/2 - offset[1] - borderWidth, 1000, mapSize[1] * 2 + 1000)) # right
                pygame.draw.rect(self.screen, self.serverData["map"]["outerColour"], (self.screenSize[0]/2 - offset[0] - 1000, self.screenSize[1]/2 - offset[1] + mapSize[1] + borderWidth, mapSize[0] * 2 + 1000, mapSize[1] + 1000)) # bottom
                pygame.draw.rect(self.screen, self.serverData["map"]["outerColour"], (self.screenSize[0]/2 - offset[0] - borderWidth - 1000, self.screenSize[1]/2 - offset[1] - 1000, 1000, mapSize[1]*2 + 1000)) # left

                # Draw Players and Features and Shots
                playerIncrementer = 0
                featuresIncrementer = 0
                for i in range(len(playerPositions) + len(featurePositions)):
                    if featuresIncrementer == len(featurePositions):
                        self.displayPlayer(playerPositions[playerIncrementer], usernamePositions[playerIncrementer], offset)
                        playerIncrementer += 1
                    elif playerIncrementer == len(playerPositions):
                        self.displayFeature(featurePositions[featuresIncrementer], offset)
                        featuresIncrementer += 1
                    elif featurePositions[featuresIncrementer][1] + featurePositions[featuresIncrementer][2][1] > playerPositions[playerIncrementer][1] + playerPositions[playerIncrementer][3][1]: # if the y + height is higher, then display it later.
                        self.displayPlayer(playerPositions[playerIncrementer], usernamePositions[playerIncrementer], offset)
                        playerIncrementer += 1
                    else:
                        self.displayFeature(featurePositions[featuresIncrementer], offset)
                        featuresIncrementer += 1


                # Display Player Coordinates
                coordinates = self.mediumFont.render(f"{int(currentPlayerInfo[0])}, {int(currentPlayerInfo[1])}", True, BLACK)
                self.screen.blit(coordinates, self.uiPadding)

                # Render leave button
                leaveBtnX, leaveBtnY = (self.screenSize[0] - self.leaveBtn.get_size()[0] - self.uiPadding[0], self.uiPadding[1])
                self.screen.blit(self.leaveBtn, (leaveBtnX, leaveBtnY))

                # Render shot cooldown
                if player["tagger"]:
                    cooldown = player["cooldown"]
                    if cooldown <= 0: cooldownText = self.mediumFont.render("READY", True, GREEN)
                    else: cooldownText = self.mediumFont.render(str(round(cooldown / self.serverData["tickRate"], 1)), True, RED)

                    self.screen.blit(cooldownText, (self.uiPadding[0], self.screenSize[1] - self.uiPadding[1] - cooldownText.get_size()[1]))

                # Render current role
                if player["tagger"]:
                    roleText = self.mediumFont.render("Tagger", True, RED)
                else:
                    roleText = self.mediumFont.render("Runner", True, BLUE)

                self.screen.blit(roleText, (self.screenSize[0] - self.uiPadding[0] - roleText.get_size()[0], self.screenSize[1] - self.uiPadding[1] - roleText.get_size()[1]))


                # Display Player Collectibles
                totalCollectibles = len(player["collectibles"])
                if totalCollectibles > 0:
                    collectibleHeight = 80
                    collectibleWidth = 80
                    topPadding = 100
                    leftPadding = 0
                    collectiblePadding = 10
                    fontHeight = self.font.render("A", True, BLACK).get_size()[1]

                    for collectible in player["collectibles"]:
                        self.screen.blit(pygame.transform.scale(self.featureIcons[collectible["name"]], (collectibleWidth - fontHeight, collectibleHeight - fontHeight)), (self.uiPadding[0] + leftPadding + fontHeight/2, topPadding))
                        text = self.font.render(f"{collectible['time'] / self.serverData['tickRate']:.2f}", True, BLACK)
                        self.screen.blit(text, (self.uiPadding[0] + leftPadding + collectibleWidth/2 - text.get_size()[0]/2, topPadding + collectibleHeight - fontHeight))

                        topPadding += collectibleHeight + collectiblePadding
                        if topPadding + collectibleHeight > self.screenSize[1] - 50: # 50 is arbitary
                            topPadding = 100
                            leftPadding += collectibleWidth + collectiblePadding

                # Display Game/Intermission Time left
                if self.serverData["inGame"]:
                    timeLeft = self.serverData["gameTime"]
                    timeLeftText = self.font.render(f"Time Left: {timeLeft:.1f}", True, BLACK)
                else:
                    timeLeft = self.serverData["intermissionTime"]
                    timeLeftText = self.font.render(f"Intermission Time Left: {timeLeft:.1f}", True, BLACK)

                timeLeftX, timeLeftY = (self.screenSize[0]/2 - timeLeftText.get_size()[0]/2, self.uiPadding[1])
                self.screen.blit(timeLeftText, (timeLeftX, timeLeftY))



                # Manage alert text
                if self.clientData["alert"] != "":
                    self.alertText = self.bigFont.render(self.clientData["alert"], True, RED)
                    self.clientData["alert"] = ""
                    self.alertWait[0] = 0
                if self.alertWait[0] != -1:
                    self.screen.blit(self.alertText, (self.screenSize[0] / 2 - self.alertText.get_size()[0] / 2, self.screenSize[1] / 2 - self.alertText.get_size()[1] / 2))
                if self.alertWait[0] > FPS:
                    self.alertWait[0] = -1



            pygame.display.flip()
            clock.tick(FPS)
            if self.menuWait[0] != -1: self.menuWait[0] += 1
            if self.alertWait[0] != -1: self.alertWait[0] += 1

        pygame.quit()

