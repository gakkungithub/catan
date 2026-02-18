from board import Board, BoardState
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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1:
                    continue
                if board.pick_town_pos_from_mouse(event.pos):
                    continue
                if board.pick_way_pos_from_mouse(event.pos):
                    continue

        board.draw()

if __name__ == "__main__":
    main()