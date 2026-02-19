from enum import Enum
import pygame
from image_manager import ImageManager

class ResourceCardType(Enum):
    TREE = 0
    BRICK = 1
    SHEEP = 2
    WHEAT = 3
    ORE = 4

class DevelopmentCardType(Enum):
    KNIGHT = 0
    ROAD = 1
    PLENTY = 2
    MONOPOLY = 3
    POINT = 4

class HandCards:
    def __init__(self, rect: pygame.Rect, color: tuple[int,int,int], player_name: str):
        self.font = pygame.font.SysFont("Arial", 24)

        self.player_name = player_name
        self.resources = [0] * 5
        self.developments = [0] * 5

        self.town_points = 0
        
        self.x = rect[0]
        self.y = rect[1]
        self.width = rect[2]
        self.height = rect[3]

        self.surface = pygame.Surface(
            (rect[2], rect[3]), pygame.SRCALPHA)
        self.color = color

        self.card_num_to_be_discarded = 0
        self.resource_images = (
            ImageManager.load("tree"), ImageManager.load("brick"), ImageManager.load("sheep"), 
            ImageManager.load("wheat"), ImageManager.load("ore")
            )
        self.development_images = (
            ImageManager.load("knight"), ImageManager.load("road"), ImageManager.load("plenty"), 
            ImageManager.load("monopoly"), ImageManager.load("point")
            )
        self.arrow_up_image = ImageManager.load("arrow")
        self.arrow_down_image = pygame.transform.rotate(self.arrow_up_image, 180)

    def draw(self, screen: pygame.Surface):
        self.surface.fill((150,150,150))
        
        surf = self.font.render(self.player_name, True, self.color)
        self.surface.blit(surf, surf.get_rect(topleft=(10, 10)))
        surf = self.font.render(f"{self.town_points + self.developments[4]} / 10", True, self.color)
        self.surface.blit(surf, surf.get_rect(topright=(self.width-10, 10)))

        # 資源カードの表示
        for i in range(5):
            img = self.resource_images[i]
            self.surface.blit(img, img.get_rect(topleft=(10+50*i, 50)))
            surf = self.font.render(str(self.resources[i]), True, self.color)
            self.surface.blit(surf, surf.get_rect(topright=(28+50*i, 90)))
            if self.card_num_to_be_discarded:
                self.surface.blit(self.arrow_up_image, self.arrow_up_image.get_rect(topright=(50*(i+1)-2, 85)))
                self.surface.blit(self.arrow_down_image, self.arrow_down_image.get_rect(topright=(50*(i+1)-2, 105)))

        # 発展カードの表示
        for i in range(5):
            img = self.development_images[i]
            self.surface.blit(img, img.get_rect(topleft=(10+50*i, 130)))
            surf = self.font.render(str(self.developments[i]), True, self.color)
            self.surface.blit(surf, surf.get_rect(topright=(28+50*i, 170)))

        screen.blit(self.surface, (self.x, self.y))

    def add_resources(self, resources_to_add: list[int]):
        self.resources = [i+j for i, j in zip(self.resources, resources_to_add)]

    def count_resources_to_be_discarded(self):
        return sum(self.resources) // 2 if sum(self.resources) >= 8 else 0