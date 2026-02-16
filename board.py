import pygame
import random

class Board:
    VERTEX_DIR: tuple[tuple[int,int]] = ((0,-2),(2,-1),(2,1),(0,2),(-2,1),(-2,-1))
    SCALEX: int = 30
    SCALEY: int = 36
    SCREEN_WIDTH: int = 1280
    SCREEN_HEIGHT: int = 720
    LINE_COLOR: tuple[int,int,int] = (0,0,0)
    BG_COLOR: tuple[int,int,int] = (0,174,239)
    NUMBER_COLOR: tuple[int,int,int] = (0,0,0)
    RESOURCE_COLORS: dict[str,tuple[int,int,int]] = {
        "tree": (0,85,46),
        "brick": (181,82,51),
        "sheep": (195,216,37),
        "wheat": (255,236,71),
        "ore": (169,169,169),
        "gold": (57,57,58),
        "dessert": (196,153,97),
    }

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        self.space_pos: tuple[tuple[int, int]] = (
                    (-4,-6),(0,-6),(4,-6),
                    (-6,-3),(-2,-3),(2,-3),(6,-3),
                    (-8,0),(-4,0),(0,0),(4,0),(8,0),
                    (-6,3),(-2,3),(2,3),(6,3),
                    (-4,6),(0,6),(4,6))
        self.resources, self.numbers = self.generate_resources_and_numbers()
        self.font = pygame.font.SysFont("Arial", 24)

    def generate_resources_and_numbers(self):
        resources = (
            ["brick"] * 3 +
            ["ore"]   * 3 +
            ["tree"]  * 4 +
            ["wheat"] * 4 +
            ["sheep"] * 4 +
            ["dessert"] * 1
        )
        random.shuffle(resources)
        dessert_index: int = resources.index("dessert")
        numbers = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]
        random.shuffle(numbers)
        numbers.insert(dessert_index, 0)
        return resources, numbers

    
    def draw(self):
        self.screen.fill(self.BG_COLOR)
        for i, pos in enumerate(self.space_pos):
            self.draw_hexagon(i, pos)
        pygame.display.flip()
        

    def draw_hexagon(self, index, center: tuple[int, int]):
        points: list[tuple[int,int]] = []
        for d in self.VERTEX_DIR:
            points.append(((center[0]+d[0])*self.SCALEX+self.SCREEN_WIDTH//2, (center[1]+d[1])*self.SCALEY+self.SCREEN_HEIGHT//2))
        
        color = self.RESOURCE_COLORS[self.resources[index]]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, self.LINE_COLOR, points, 2)

        if (number := self.numbers[index]):
            number_surf: pygame.Surface = self.font.render(str(number), True, self.NUMBER_COLOR)
            rect = number_surf.get_rect(center=(center[0]*self.SCALEX+self.SCREEN_WIDTH//2, center[1]*self.SCALEY+self.SCREEN_HEIGHT//2))
            self.screen.blit(number_surf, rect)


