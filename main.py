from board import Board
import pygame

def main():
    clock = pygame.time.Clock()
    board = Board()

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                return

        board.draw()
        
if __name__ == "__main__":
    main()