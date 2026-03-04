import pygame, json

def getPlayerDisplayInfo(currentUsername, font, playerData, serverData):
    width = height = serverData["player"]["size"]
    usernamePositions = []
    playerPositions = []

    for player in playerData:
        xPos, yPos = player["position"]
        username = player["username"]
        renderedUsername = font.render(username, True, (0,0,0))
        xUsername = xPos + (width / 2) - (renderedUsername.get_size()[0] / 2)
        yUsername = yPos - 10 - renderedUsername.get_size()[1]

        if username == currentUsername:
            usernamePositions.insert(0, [xUsername, yUsername, renderedUsername])
            playerPositions.insert(0, [xPos, yPos, player["colour"]])
        else:
            usernamePositions.append([xUsername, yUsername, renderedUsername])
            playerPositions.append([xPos, yPos, player["colour"]])

    if len(playerPositions) > 2:
        # sorting based off of the y value.
        tempPlayerPositions, tempUsernamePositions = [list(positions) for positions in zip(*sorted(zip(playerPositions[1:], usernamePositions[1:]), key=lambda data: -data[0][1]))]
        playerPositions = [playerPositions[0]] + tempPlayerPositions
        usernamePositions = [usernamePositions[0]] + tempUsernamePositions

    return playerPositions[::-1], usernamePositions[::-1]


def render(client, playerData, serverData):
    W, H = 800, 600
    WHITE, BLACK = (255,255,255), (0,0,0)
    FPS = 30
    velocity = [0, 0]

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
        
        width = height = serverData["player"]["size"]

        playerPositions, usernamePositions = getPlayerDisplayInfo(client.username, font, playerData, serverData)
        offset = playerPositions[-1]

        # Draw Map
        mapSize = serverData["map"]
        borderWidth = 2
        pygame.draw.rect(screen, BLACK, (screen.get_size()[0] / 2 - offset[0] - borderWidth, screen.get_size()[1] / 2 - offset[1] - borderWidth, mapSize[0] + borderWidth * 2, mapSize[1] + borderWidth * 2), borderWidth)

        # Draw Players
        for i in range(len(playerPositions)):
            playerInfo = playerPositions[i]
            usernameInfo = usernamePositions[i]
            playerX = playerInfo[0] - offset[0] + screen.get_size()[0] / 2
            playerY = playerInfo[1] - offset[1] + screen.get_size()[1] / 2
            usernameX = usernameInfo[0] - offset[0] + screen.get_size()[0] / 2
            usernameY = usernameInfo[1] - offset[1] + screen.get_size()[1] / 2

            screen.blit(usernameInfo[2], (usernameX, usernameY))
            pygame.draw.rect(screen, playerInfo[2], (playerX, playerY, width, height))


        #Display Player Coordinates
        coordinates = bigFont.render(f"{int(offset[0])}, {int(offset[1])}", True, BLACK)
        screen.blit(coordinates, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

