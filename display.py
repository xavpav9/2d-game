import pygame, json

def getPlayerDisplayInfo(currentUsername, font, playerData, serverData):
    usernamePositions = []
    playerPositions = []

    for player in playerData:
        width = height = player["size"]
        xPos, yPos = player["position"]
        username = player["username"]
        renderedUsername = font.render(username, True, (0,0,0))
        xUsername = xPos + (width / 2) - (renderedUsername.get_size()[0] / 2)
        yUsername = yPos - 10 - renderedUsername.get_size()[1]

        usernameInfo = [xUsername, yUsername, renderedUsername]
        playerInfo = [xPos, yPos, player["colour"], width, player["hidden"]]
        if username == currentUsername:
            usernamePositions.insert(0, usernameInfo)
            playerPositions.insert(0, playerInfo)
        else:
            usernamePositions.append(usernameInfo)
            playerPositions.append(playerInfo)

    if len(playerPositions) > 2:
        # sorting based off of the y value.
        tempPlayerPositions, tempUsernamePositions = [list(positions) for positions in zip(*sorted(zip(playerPositions[1:], usernamePositions[1:]), key=lambda data: -(data[0][1] + data[0][3])))]
        playerPositions = [playerPositions[0]] + tempPlayerPositions
        usernamePositions = [usernamePositions[0]] + tempUsernamePositions

    return playerPositions[::-1], usernamePositions[::-1]

def getFeaturesDisplayInfo(featuresData):
    featurePositions = []
    for feature in featuresData:
        xPos, yPos = feature["position"]
        size = feature["size"]
        name = feature["name"]
        featurePositions.append([xPos, yPos, size, name])

    return sorted(featurePositions, key=lambda data: data[1] + data[2])


def displayPlayer(screen, playerInfo, usernameInfo, offset):
    # playerInfo = [x, y, colour, size, hiddenUsername]
    width = height = playerInfo[3]
    playerX = playerInfo[0] - offset[0] + screen.get_size()[0] / 2
    playerY = playerInfo[1] - offset[1] + screen.get_size()[1] / 2
    if not playerInfo[4]:
        usernameX = usernameInfo[0] - offset[0] + screen.get_size()[0] / 2
        usernameY = usernameInfo[1] - offset[1] + screen.get_size()[1] / 2
        screen.blit(usernameInfo[2], (usernameX, usernameY))

    pygame.draw.rect(screen, playerInfo[2], (playerX, playerY, width, height))

def displayFeature(screen, featureInfo, featureIcons, offset):
    # featureInfo = [x, y, size, name]
    width = height = featureInfo[2]
    featureX = featureInfo[0] - offset[0] + screen.get_size()[0] / 2
    featureY = featureInfo[1] - offset[1] + screen.get_size()[1] / 2

    icon = featureIcons["noTexture"]
    if featureInfo[3] in featureIcons.keys(): icon = featureIcons[featureInfo[3]]
    scaledIcon = pygame.transform.scale(icon, (width, height))
    screen.blit(scaledIcon, (featureX, featureY))

def render(client, playerData, serverData):
    W, H = 800, 600
    WHITE, BLACK = (255,255,255), (0,0,0)
    FPS = 30
    velocity = [0, 0]
    featureIcons = {"noTexture": pygame.image.load("res/noTexture.png"), "rock": pygame.image.load("res/rock.png")}

    pygame.init()

    typeface = "freemono"
    availableFonts = pygame.font.get_fonts()
    if typeface not in availableFonts: typeface = availableFonts[0]

    clock = pygame.time.Clock()
    bigFont = pygame.font.SysFont(typeface, 40, True, True)
    font = pygame.font.SysFont(typeface, 20, True, True)
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Game")


    running = True
    while running:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False
            elif evt.type == pygame.KEYDOWN:
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

                if newData:
                    client.sendData("v" + json.dumps(velocity))
            elif evt.type == pygame.KEYUP:
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



        screen.fill(WHITE)

        playerPositions, usernamePositions = getPlayerDisplayInfo(client.username, font, playerData, serverData)
        featurePositions = getFeaturesDisplayInfo(serverData["features"])
        offset = playerPositions[-1]

        # Draw Map
        mapSize = serverData["map"]
        borderWidth = 2
        pygame.draw.rect(screen, BLACK, (screen.get_size()[0] / 2 - offset[0] - borderWidth, screen.get_size()[1] / 2 - offset[1] - borderWidth, mapSize[0] + borderWidth * 2, mapSize[1] + borderWidth * 2), borderWidth)

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
            elif featurePositions[featuresIncrementer][1] > playerPositions[playerIncrementer][1]:
                displayFeature(screen, featurePositions[featuresIncrementer], featureIcons, offset)
                featuresIncrementer += 1
            else:
                displayPlayer(screen, playerPositions[playerIncrementer], usernamePositions[playerIncrementer], offset)
                playerIncrementer += 1


        #Display Player Coordinates
        coordinates = bigFont.render(f"{int(offset[0])}, {int(offset[1])}", True, BLACK)
        screen.blit(coordinates, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

