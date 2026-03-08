import pygame, json
from time import sleep

def getPlayerDisplayInfo(currentUsername, font, playerData, serverData):
    # playerInfo = [x, y, colour, size, hiddenUsername] size=width,height
    usernamePositions = []
    playerPositions = []

    for player in playerData:
        width, height = player["size"]
        xPos, yPos = player["position"]
        username = player["username"]
        renderedUsername = font.render(username, True, (0,0,0))
        xUsername = xPos + (width / 2) - (renderedUsername.get_size()[0] / 2)
        yUsername = yPos - 10 - renderedUsername.get_size()[1]

        usernameInfo = [xUsername, yUsername, renderedUsername]
        playerInfo = [xPos, yPos, player["colour"], (width, height), player["hidden"]]
        if username == currentUsername:
            usernamePositions.insert(0, usernameInfo)
            playerPositions.insert(0, playerInfo)
        else:
            usernamePositions.append(usernameInfo)
            playerPositions.append(playerInfo)

    if len(playerPositions) > 2:
        # sorting based off of the y value + playerSize.
        tempPlayerPositions, tempUsernamePositions = [list(positions) for positions in zip(*sorted(zip(playerPositions[1:], usernamePositions[1:]), key=lambda data: data[0][1] + data[0][3], reverse=True))]
        playerPositions = [playerPositions[0]] + tempPlayerPositions
        usernamePositions = [usernamePositions[0]] + tempUsernamePositions

    return playerPositions[::-1], usernamePositions[::-1]

def getFeaturesDisplayInfo(featuresData):
    # featureInfo = [x, y, size, name] size=width,height
    featurePositions = []
    for feature in featuresData:
        xPos, yPos = feature["position"]
        width, height = feature["size"]
        name = feature["name"]
        featurePositions.append([xPos, yPos, (width, height), name])

    # sorting based off of the y value + playerSize.
    return sorted(featurePositions, key=lambda data: data[1] + data[2][1])


def displayPlayer(screen, playerInfo, usernameInfo, offset):
    # playerInfo = [x, y, colour, size, hiddenUsername] size=width,height
    width, height = playerInfo[3]
    playerX = playerInfo[0] - offset[0] + screen.get_size()[0] / 2
    playerY = playerInfo[1] - offset[1] + screen.get_size()[1] / 2
    if not playerInfo[4]:
        usernameX = usernameInfo[0] - offset[0] + screen.get_size()[0] / 2
        usernameY = usernameInfo[1] - offset[1] + screen.get_size()[1] / 2
        screen.blit(usernameInfo[2], (usernameX, usernameY))

    pygame.draw.rect(screen, playerInfo[2], (playerX, playerY, width, height))

def displayFeature(screen, featureInfo, featureIcons, offset):
    # featureInfo = [x, y, size, name] size=width,height
    width, height = featureInfo[2]
    featureX = featureInfo[0] - offset[0] + screen.get_size()[0] / 2
    featureY = featureInfo[1] - offset[1] + screen.get_size()[1] / 2

    icon = featureIcons["noTexture"]
    if featureInfo[3] in featureIcons.keys(): icon = featureIcons[featureInfo[3]]
    scaledIcon = pygame.transform.scale(icon, (width, height))
    screen.blit(scaledIcon, (featureX, featureY))

def render(client, playerData, serverData, clientData):
    W, H = 800, 600
    WHITE, BLACK, RED, GREEN, BLUE = (255,255,255), (0,0,0), (255,0,0), (0,255,0), (0,0,255)
    FPS = 30
    velocity = [0, 0] # x and y velocities
    clickPos = [0, 0] # position of click so that it is known when user releases mouse click
    btnPadding = [20, 10] # x and y padding of buttons on menu screen
    uiPadding = [10, 10] # x and y padding for ui on game screen
    menuWait = [-1, False] # for bottomText pop ups. index 0: current frame since started, index 2: whether the client is trying to connect to the server or not
    alertWait = [-1] # for game alerts. index 0: current frame since started
    ctrl = False # whether ctrl is being held
    validUsernameCharacters = "abcdefghijklmnopqrstuvwxyz1234567890_- "
    featureIcons = {"noTexture": pygame.image.load("res/noTexture.png"), "rock": pygame.image.load("res/rock.png"), "bush": pygame.image.load("res/bush.png")}
    leaveBtn = pygame.transform.scale(pygame.image.load("res/leave.svg"), (30, 40))

    pygame.init()

    typeface = "freemono"
    availableFonts = pygame.font.get_fonts()
    if typeface not in availableFonts: typeface = availableFonts[0]

    clock = pygame.time.Clock()
    bigFont = pygame.font.SysFont(typeface, 40, True, True)
    font = pygame.font.SysFont(typeface, 20, True, True)
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Game")

    title = bigFont.render("Tag", True, BLACK)
    bottomText = font.render("", True, BLACK)
    alertText = bigFont.render("", True, RED)
    playBtn = font.render("Play", True, BLACK)
    quitBtn = font.render("Quit", True, RED)


    while clientData["running"]:
        screenSize = screen.get_size()
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                clientData["running"] = False
            elif evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_LCTRL:
                    ctrl = True
                elif clientData["inMenu"]:
                    if evt.unicode.lower() in validUsernameCharacters and (menuWait[0] == -1 or not menuWait[1]):
                        if len(client.username) < 15: client.username += evt.unicode
                    elif evt.key == pygame.K_BACKSPACE and (menuWait[0] == -1 or not menuWait[1]):
                        if ctrl: client.username = ""
                        elif len(client.username) > 0: client.username = client.username[:-1]
                    elif evt.key == pygame.K_RETURN: # Connect to game when <CR> is pressed
                        if len(client.username) >= 2:
                            clientData["inMenu"] = False
                            bottomText = font.render("Connecting to server...", True, GREEN)
                            menuWait = [FPS/4, True]
                        else:
                            bottomText = font.render("Username too short", True, RED)
                            menuWait = [0, False]

                    elif evt.key == pygame.K_ESCAPE: # Quit game when Esc is pressed in menu
                        clientData["running"] = False

                elif menuWait[0] == -1:
                    newData = False
                    if evt.key == pygame.K_a:
                        newData = True
                        velocity[0] = -1
                    elif evt.key == pygame.K_d:
                        newData = True
                        velocity[0] = 1
                    elif evt.key == pygame.K_w:
                        newData = True
                        velocity[1] = -1
                    elif evt.key == pygame.K_s:
                        newData = True
                        velocity[1] = 1
                    elif evt.key == pygame.K_ESCAPE: # Return to menu when Esc is pressed in game
                        client.close()
                        clientData["inMenu"] = True
                        bottomText = font.render("Disconnected from server.", True, RED)
                        menuWait = [0, False]

                    if newData:
                        client.sendData("v" + json.dumps(velocity))

            elif evt.type == pygame.KEYUP:
                if evt.key == pygame.K_LCTRL:
                    ctrl = False
                elif clientData["inMenu"]:
                    pass
                else:
                    newData = False
                    if evt.key == pygame.K_a and velocity[0] != 1:
                        newData = True
                        velocity[0] = 0
                    elif evt.key == pygame.K_d and velocity[0] != -1:
                        newData = True
                        velocity[0] = 0
                    elif evt.key == pygame.K_w and velocity[1] != 1:
                        newData = True
                        velocity[1] = 0
                    elif evt.key == pygame.K_s and velocity[1] != -1:
                        newData = True
                        velocity[1] = 0

                    if newData:
                        client.sendData("v" + json.dumps(velocity))

            elif evt.type == pygame.MOUSEBUTTONDOWN:
                clickPos = pygame.mouse.get_pos()

            elif evt.type == pygame.MOUSEBUTTONUP:
                if clientData["inMenu"]:
                    width, height = screenSize
                    # This refers to the x and y of the top left of the text for each one.
                    playBtnX, playBtnY = (width/2 - playBtn.get_size()[0]/2, height/2)
                    titleBtnX, titleBtnY = (width/2 - title.get_size()[0]/2, height/6)
                    quitBtnX, quitBtnY = (width/2 - quitBtn.get_size()[0]/2, 3*height/5)

                    if clickPos[0] - (playBtnX - btnPadding[0]) < (playBtn.get_size()[0] + btnPadding[0] * 2) and clickPos[1] - (playBtnY - btnPadding[1]) < (playBtn.get_size()[1] + btnPadding[1] * 2):
                        if len(client.username) >= 2:
                            clientData["inMenu"] = False
                            bottomText = font.render("Connecting to server...", True, GREEN)
                            menuWait = [FPS/4, True]
                        else:
                            bottomText = font.render("Username too short", True, RED)
                            menuWait = [0, False]

                    elif clickPos[0] - (quitBtnX - btnPadding[0]) < (quitBtn.get_size()[0] + btnPadding[0] * 2) and clickPos[1] - (quitBtnY - btnPadding[1]) < (quitBtn.get_size()[1] + btnPadding[1] * 2):
                        clientData["running"] = False

                else:
                    leaveBtnX, leaveBtnY = (screenSize[0] - leaveBtn.get_size()[0] - uiPadding[0], uiPadding[1])

                    if clickPos[0] - leaveBtnX < leaveBtn.get_size()[0] and clickPos[1] - leaveBtnY < leaveBtn.get_size()[1]:
                        client.close()
                        clientData["inMenu"] = True
                        bottomText = font.render("Disconnected from server.", True, RED)
                        menuWait = [0, False]


        screen.fill(WHITE)

        if not clientData["running"]: break

        if clientData["inMenu"] or menuWait[0] != -1:
            # -- Display Menu -- #

            width, height = screenSize
            usernameDisplay = font.render(client.username, True, BLUE)

            titleBtnX, titleBtnY = (width/2 - title.get_size()[0]/2, height/6)
            screen.blit(title, (titleBtnX, titleBtnY))
            pygame.draw.line(screen, BLACK, (titleBtnX, titleBtnY+title.get_size()[1]), (titleBtnX+title.get_size()[0], titleBtnY+title.get_size()[1]), 4)

            screen.blit(usernameDisplay, (width/2 - usernameDisplay.get_size()[0]/2, height/3))

            playBtnX, playBtnY = (width/2 - playBtn.get_size()[0]/2, height/2)
            screen.blit(playBtn, (playBtnX, playBtnY))
            pygame.draw.rect(screen, BLACK, (playBtnX - btnPadding[0], playBtnY - btnPadding[1], playBtn.get_size()[0] + btnPadding[0] * 2, playBtn.get_size()[1] + btnPadding[1] * 2), 4, 5)

            quitBtnX, quitBtnY = (width/2 - quitBtn.get_size()[0]/2, 3*height/5)
            screen.blit(quitBtn, (quitBtnX, quitBtnY))
            pygame.draw.rect(screen, BLACK, (quitBtnX - btnPadding[0], quitBtnY - btnPadding[1], quitBtn.get_size()[0] + btnPadding[0] * 2, quitBtn.get_size()[1] + btnPadding[1] * 2), 4, 5)

            if menuWait[0] != -1:
                screen.blit(bottomText, (width/2-bottomText.get_size()[0]/2, 4*height/5))
            if menuWait[0] >= FPS:
                menuWait[0] = -1
                if menuWait[1]: # connecting to server = True
                    while len(playerData) == 0:
                        sleep(0.1)
                        if clientData["inMenu"]:
                            # unsuccessful attempt to connect to server, so main.py has set the "inMenu" flag back to true
                            bottomText = font.render(clientData["problem"], True, RED)
                            menuWait = [0, False]
                            break

        else:
            # -- Display Current Game -- #

            playerPositions, usernamePositions = getPlayerDisplayInfo(client.username, font, playerData, serverData)
            featurePositions = getFeaturesDisplayInfo(serverData["features"])
            offset = [playerPositions[-1][i] + playerPositions[-1][3][i] / 2 for i in range(2)]

            # Draw Map
            mapSize = serverData["map"]
            borderWidth = 2
            pygame.draw.rect(screen, BLACK, (screenSize[0] / 2 - offset[0] - borderWidth, screenSize[1] / 2 - offset[1] - borderWidth, mapSize[0] + borderWidth * 2, mapSize[1] + borderWidth * 2), borderWidth)

            # Draw Players and Features
            playerIncrementer = 0
            featuresIncrementer = 0
            for i in range(len(playerPositions) + len(featurePositions)):
                if featuresIncrementer == len(featurePositions):
                    displayPlayer(screen, playerPositions[playerIncrementer], usernamePositions[playerIncrementer], offset)
                    playerIncrementer += 1
                elif playerIncrementer == len(playerPositions):
                    displayFeature(screen, featurePositions[featuresIncrementer], featureIcons, offset)
                    featuresIncrementer += 1
                elif featurePositions[featuresIncrementer][1] + featurePositions[featuresIncrementer][2][1] > playerPositions[playerIncrementer][1] + playerPositions[playerIncrementer][3][1]: # if the y + height is higher, then display it later.
                    displayPlayer(screen, playerPositions[playerIncrementer], usernamePositions[playerIncrementer], offset)
                    playerIncrementer += 1
                else:
                    displayFeature(screen, featurePositions[featuresIncrementer], featureIcons, offset)
                    featuresIncrementer += 1


            # Display Player Coordinates
            coordinates = bigFont.render(f"{int(playerPositions[-1][0])}, {int(playerPositions[-1][1])}", True, BLACK)
            screen.blit(coordinates, uiPadding)

            # Render leave button
            leaveBtnX, leaveBtnY = (screenSize[0] - leaveBtn.get_size()[0] - uiPadding[0], uiPadding[1])
            screen.blit(leaveBtn, (leaveBtnX, leaveBtnY))

            # Manage alert text
            if clientData["alert"] != "":
                alertText = bigFont.render(clientData["alert"], True, RED)
                clientData["alert"] = ""
                alertWait[0] = 0
            if alertWait[0] != -1:
                screen.blit(alertText, (screenSize[0] / 2 - alertText.get_size()[0] / 2, screenSize[1] / 2 - alertText.get_size()[1] / 2))
            if alertWait[0] > FPS:
                alertWait[0] = -1



        pygame.display.flip()
        clock.tick(FPS)
        if menuWait[0] != -1: menuWait[0] += 1
        if alertWait[0] != -1: alertWait[0] += 1

    pygame.quit()

