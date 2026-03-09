import pygame, json, math
from time import sleep

def getPlayerDisplayInfo(currentUsername, font, playerData, serverData):
    # playerInfo = [x, y, colour, size, hiddenUsername] size=width,height
    usernamePositions = []
    playerPositions = []

    for player in playerData:
        width, height = player["size"]
        xPos, yPos = player["position"]
        shots = player["shots"]
        username = player["username"]
        usernameColour = (0, 0, 255)
        if player["tagger"]: usernameColour = (255, 0, 0)
        renderedUsername = font.render(username, True, usernameColour)
        xUsername = xPos + (width / 2) - (renderedUsername.get_size()[0] / 2)
        yUsername = yPos - 10 - renderedUsername.get_size()[1]

        usernameInfo = [xUsername, yUsername, renderedUsername]
        playerInfo = [xPos, yPos, player["colour"], (width, height), player["hidden"], shots]

        if currentUsername == username:
            currentPlayerInfo = playerInfo

        usernamePositions.append(usernameInfo)
        playerPositions.append(playerInfo)

    # sorting based off of the y value + playerSize.
    playerPositions, usernamePositions = [list(positions) for positions in zip(*sorted(zip(playerPositions, usernamePositions), key=lambda data: data[0][1] + data[0][3][1]))]

    return playerPositions, usernamePositions, currentPlayerInfo

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
    # playerInfo = [x, y, colour, size, hiddenUsername, shots] size=width,height, shots={angle, size}
    playerWidth, playerHeight = playerInfo[3]
    playerX = playerInfo[0] - offset[0] + screen.get_size()[0] / 2
    playerY = playerInfo[1] - offset[1] + screen.get_size()[1] / 2
    
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

        pygame.draw.rect(screen, (255, 0, 0), (position[0], position[1], shot["size"][0], shot["size"][1]))

    if not playerInfo[4]:
        usernameX = usernameInfo[0] - offset[0] + screen.get_size()[0] / 2
        usernameY = usernameInfo[1] - offset[1] + screen.get_size()[1] / 2
        screen.blit(usernameInfo[2], (usernameX, usernameY))

    pygame.draw.rect(screen, playerInfo[2], (playerX, playerY, playerWidth, playerHeight))

def displayFeature(screen, featureInfo, featureIcons, offset):
    # featureInfo = [x, y, size, name] size=width,height
    width, height = featureInfo[2]
    featureX = featureInfo[0] - offset[0] + screen.get_size()[0] / 2
    featureY = featureInfo[1] - offset[1] + screen.get_size()[1] / 2

    icon = featureIcons["noTexture"]
    if featureInfo[3] in featureIcons.keys(): icon = featureIcons[featureInfo[3]]
    scaledIcon = pygame.transform.scale(icon, (width, height))
    screen.blit(scaledIcon, (featureX, featureY))

def calculateAngle(x, y):
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
    mediumFont = pygame.font.SysFont(typeface, 30, True, True)
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
                    if evt.key == pygame.K_a or evt.key == pygame.K_LEFT:
                        newData = True
                        velocity[0] = -1
                    elif evt.key == pygame.K_d or evt.key == pygame.K_RIGHT:
                        newData = True
                        velocity[0] = 1
                    elif evt.key == pygame.K_w or evt.key == pygame.K_UP:
                        newData = True
                        velocity[1] = -1
                    elif evt.key == pygame.K_s or evt.key == pygame.K_DOWN:
                        newData = True
                        velocity[1] = 1
                    elif evt.key == pygame.K_ESCAPE: # Return to menu when Esc is pressed in game
                        client.close()
                        clientData["inMenu"] = True
                        bottomText = font.render("Disconnected from server.", True, RED)
                        menuWait = [0, False]
                    elif evt.key == pygame.K_SPACE:
                        x = velocity[0]
                        y = -velocity[1]

                        angle = calculateAngle(x, y)

                        client.sendData("s" + json.dumps([angle]))

                    if newData:
                        client.sendData("v" + json.dumps(velocity))

            elif evt.type == pygame.KEYUP:
                if evt.key == pygame.K_LCTRL:
                    ctrl = False
                elif clientData["inMenu"]:
                    pass
                else:
                    newData = False
                    if (evt.key == pygame.K_a or evt.key == pygame.K_LEFT) and velocity[0] != 1:
                        newData = True
                        velocity[0] = 0
                    elif (evt.key == pygame.K_d or evt.key == pygame.K_RIGHT) and velocity[0] != -1:
                        newData = True
                        velocity[0] = 0
                    elif (evt.key == pygame.K_w or evt.key == pygame.K_UP) and velocity[1] != 1:
                        newData = True
                        velocity[1] = 0
                    elif (evt.key == pygame.K_s or evt.key == pygame.K_DOWN) and velocity[1] != -1:
                        newData = True
                        velocity[1] = 0

                    if newData:
                        client.sendData("v" + json.dumps(velocity))

            elif evt.type == pygame.MOUSEBUTTONDOWN:
                clickPos = pygame.mouse.get_pos()
                if not clientData["inMenu"]:
                    x = clickPos[0] - screenSize[0] / 2
                    y = screenSize[1] / 2 - clickPos[1]
                    angle = calculateAngle(x, y)

                    client.sendData("s" + json.dumps([angle]))

            elif evt.type == pygame.MOUSEBUTTONUP:
                if clientData["inMenu"]:
                    width, height = screenSize
                    # This refers to the x and y of the top left of the text for each one.
                    playBtnX, playBtnY = (width/2 - playBtn.get_size()[0]/2, height/2)
                    titleBtnX, titleBtnY = (width/2 - title.get_size()[0]/2, height/6)
                    quitBtnX, quitBtnY = (width/2 - quitBtn.get_size()[0]/2, 3*height/5)

                    if 0 < clickPos[0] - (playBtnX - btnPadding[0]) < (playBtn.get_size()[0] + btnPadding[0] * 2) and 0 < clickPos[1] - (playBtnY - btnPadding[1]) < (playBtn.get_size()[1] + btnPadding[1] * 2):
                        if len(client.username) >= 2:
                            clientData["inMenu"] = False
                            bottomText = font.render("Connecting to server...", True, GREEN)
                            menuWait = [FPS/4, True]
                        else:
                            bottomText = font.render("Username too short", True, RED)
                            menuWait = [0, False]

                    elif 0 < clickPos[0] - (quitBtnX - btnPadding[0]) < (quitBtn.get_size()[0] + btnPadding[0] * 2) and 0 < clickPos[1] - (quitBtnY - btnPadding[1]) < (quitBtn.get_size()[1] + btnPadding[1] * 2):
                        clientData["running"] = False

                else:
                    leaveBtnX, leaveBtnY = (screenSize[0] - leaveBtn.get_size()[0] - uiPadding[0], uiPadding[1])

                    if 0 < clickPos[0] - leaveBtnX < leaveBtn.get_size()[0] and 0 < clickPos[1] - leaveBtnY < leaveBtn.get_size()[1]:
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

            for otherPlayer in playerData:
                if otherPlayer["username"] == client.username:
                    player = otherPlayer
                    break

            playerPositions, usernamePositions, currentPlayerInfo = getPlayerDisplayInfo(client.username, font, playerData, serverData)
            featurePositions = getFeaturesDisplayInfo(serverData["features"])
            offset = [currentPlayerInfo[i] + currentPlayerInfo[3][i] / 2 for i in range(2)]

            # Draw Map
            mapSize = serverData["map"]
            borderWidth = 2
            pygame.draw.rect(screen, BLACK, (screenSize[0] / 2 - offset[0] - borderWidth, screenSize[1] / 2 - offset[1] - borderWidth, mapSize[0] + borderWidth * 2, mapSize[1] + borderWidth * 2), borderWidth)

            # Draw Players and Features and Shots
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
            coordinates = mediumFont.render(f"{int(currentPlayerInfo[0])}, {int(currentPlayerInfo[1])}", True, BLACK)
            screen.blit(coordinates, uiPadding)

            # Render leave button
            leaveBtnX, leaveBtnY = (screenSize[0] - leaveBtn.get_size()[0] - uiPadding[0], uiPadding[1])
            screen.blit(leaveBtn, (leaveBtnX, leaveBtnY))

            # Render shot cooldown
            if player["tagger"]:
                cooldown = player["cooldown"]
                if cooldown <= 0: cooldownText = mediumFont.render("READY", True, GREEN)
                else: cooldownText = mediumFont.render(str(round(cooldown / serverData["tickRate"], 1)), True, RED)

                screen.blit(cooldownText, (uiPadding[0], screenSize[1] - uiPadding[1] - cooldownText.get_size()[1]))

            # Render current role
            if player["tagger"]:
                roleText = mediumFont.render("Tagger", True, RED)
            else:
                roleText = mediumFont.render("Runner", True, BLUE)

            screen.blit(roleText, (screenSize[0] - uiPadding[0] - roleText.get_size()[0], screenSize[1] - uiPadding[1] - roleText.get_size()[1]))



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

