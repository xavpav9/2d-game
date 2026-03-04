import pygame

"""
TODO:
    - Make username display
    - Remove black rectangle at top left of screen
    - Make the getPlayerDisplayInfo actually find the correct current player
    - add to server a colour randomiser for each player

"""

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
        playerPositions = playerPositions[0] + sorted(playerPositions[1:], key=lambda a,b: b[1] - a[1])
        usernamePositions = usernamePositions[0] + sorted(usernamePositions[1:], key=lambda a,b: b[1] - a[1])

    return playerPositions[::-1], usernamePositions[::-1]


def render(client, playerData, serverData):
    W, H = 800, 600
    WHITE, BLACK = (255,255,255), (0,0,0)
    FPS = 30

    pygame.init()

    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Game")


    running = True
    while running:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False

        screen.fill(WHITE)
        
        width = height = serverData["player"]["size"]
        font = pygame.font.SysFont("freemono", int(width * 1.5), True, True)

        playerPositions, usernamePositions = getPlayerDisplayInfo(client.username, font, playerData, serverData)
        offset = playerPositions[-1]

        for i in range(len(playerPositions)):
            playerInfo = playerPositions[i]
            usernameInfo = usernamePositions[i]
            playerX = playerInfo[0] - offset[0] + screen.get_size()[0] / 2
            playerY = playerInfo[1] - offset[1] + screen.get_size()[1] / 2
            usernameX = usernameInfo[0] - offset[0] + screen.get_size()[0] / 2
            usernameY = usernameInfo[1] - offset[1] + screen.get_size()[1] / 2

            screen.blit(usernameInfo[2], (usernameX, usernameY))
            pygame.draw.rect(screen, playerInfo[2], (playerX, playerY, width, height))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

