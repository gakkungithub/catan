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
        
        self.x = rect[0]
        self.y = rect[1]

        self.surface = pygame.Surface(
            (rect[2], rect[3]), pygame.SRCALPHA)
        self.color = color

        self.resource_images = (
            ImageManager.load("tree"), ImageManager.load("brick"), ImageManager.load("sheep"), 
            ImageManager.load("wheat"), ImageManager.load("ore")
            )
        self.development_images = (
            ImageManager.load("knight"), ImageManager.load("road"), ImageManager.load("plenty"), 
            ImageManager.load("monopoly"), ImageManager.load("point")
            )
    
    def draw(self, screen: pygame.Surface):
        self.surface.fill((120,120,120))
        # 資源カードの表示
        surf = self.font.render(self.player_name, True, self.color)
        self.surface.blit(surf, surf.get_rect(topleft=(10, 10)))

        for i in range(5):
            img = self.resource_images[i]
            self.surface.blit(img, img.get_rect(topleft=(10+50*i, 50)))
            surf = self.font.render(f"×{self.resources[i]}", True, self.color)
            self.surface.blit(surf, surf.get_rect(topleft=(10+50*i, 90)))

        # 発展カードの表示
        for i in range(5):
            img = self.development_images[i]
            self.surface.blit(img, img.get_rect(topleft=(10+50*i, 130)))
            surf = self.font.render(f"×{self.developments[i]}", True, self.color)
            self.surface.blit(surf, surf.get_rect(topleft=(10+50*i, 170)))

        screen.blit(self.surface, (self.x, self.y))