from enum import IntEnum
import pygame
from image_manager import ImageManager

class ResourceCardType(IntEnum):
    TREE = 0
    BRICK = 1
    SHEEP = 2
    WHEAT = 3
    ORE = 4

class DevelopmentCardType(IntEnum):
    KNIGHT = 0
    ROAD = 1
    PLENTY = 2
    MONOPOLY = 3
    POINT = 4

class ActionType(IntEnum):
    ROADBUILD = 0
    TOWNBUILD = 1
    CITYBUILD = 2
    DEVELOPMENT = 3
    TRADE = 4

class HandCards:
    FONT_SIZE = 24
    BUTTON_FONT_SIZE = 10
    BUTTON_BG_COLOR = (100,100,100)
    BUTTON_RADIUS = 5

    def __init__(self, rect: pygame.Rect, color: tuple[int,int,int], player_name: str):
        self.font = pygame.font.SysFont("Arial", self.FONT_SIZE)
        self.button_font = pygame.font.SysFont("Arial", self.BUTTON_FONT_SIZE)

        self.player_name = player_name
        self.resources = [0] * 5
        self.developments = [0] * 5

        self.town_points = 0
        
        self.x = rect[0]
        self.y = rect[1]
        self.card_width = rect[2]-110
        self.height = rect[3]

        self.card_surface = pygame.Surface(
            (rect[2]-110, rect[3]), pygame.SRCALPHA)
        
        self.action_surface = pygame.Surface(
            (100, rect[3]), pygame.SRCALPHA)

        self.color = color

        self.actions = (self.get_button_rect("NEW ROAD", (50,30)), self.get_button_rect("NEW TOWN", (50,30+self.BUTTON_FONT_SIZE+25)), self.get_button_rect("NEW CITY", (50,30+(self.BUTTON_FONT_SIZE+25)*2)),
                        self.get_button_rect("DEVELOPMENT", (50,30+(self.BUTTON_FONT_SIZE+25)*3)), self.get_button_rect("TRADE", (50,30+(self.BUTTON_FONT_SIZE+25)*4)))
        self.possible_actions: list[tuple[int, tuple[pygame.Surface, pygame.Rect, pygame.Rect]]] = []

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

        self.crnt_action = "normal"

    def get_button_rect(self, name: str, pos: tuple[int,int]):
        surf = self.button_font.render(name, True, self.color)
        rect = surf.get_rect()
        button_rect = rect.inflate(10*2,7*2)
        button_rect.center = pos
        rect.center = button_rect.center
        return surf, rect, button_rect

    def draw(self, screen: pygame.Surface):
        self.card_surface.fill((150,150,150))
        
        surf = self.font.render(self.player_name, True, self.color)
        self.card_surface.blit(surf, surf.get_rect(topleft=(10, 10)))
        surf = self.font.render(f"{self.town_points + self.developments[4]} / 10", True, self.color)
        self.card_surface.blit(surf, surf.get_rect(topright=(self.card_width-10, 10)))

        # 資源カードの表示
        for i in range(5):
            img = self.resource_images[i]
            self.card_surface.blit(img, img.get_rect(topleft=(10+50*i, 50)))
            surf = self.font.render(str(self.resources[i]), True, self.color)
            self.card_surface.blit(surf, surf.get_rect(topright=(28+50*i, 90)))
            if self.card_num_to_be_discarded:
                self.card_surface.blit(self.arrow_up_image, self.arrow_up_image.get_rect(topright=(50*(i+1)-2, 85)))
                self.card_surface.blit(self.arrow_down_image, self.arrow_down_image.get_rect(topright=(50*(i+1)-2, 105)))

        # 発展カードの表示
        for i in range(5):
            img = self.development_images[i]
            self.card_surface.blit(img, img.get_rect(topleft=(10+50*i, 130)))
            surf = self.font.render(str(self.developments[i]), True, self.color)
            self.card_surface.blit(surf, surf.get_rect(topright=(28+50*i, 170)))

        screen.blit(self.card_surface, (self.x, self.y))

        if self.crnt_action == "action":
            self.action_surface.fill((255,255,255))
            for _, (button_surf, button_label, button_rect) in self.possible_actions:
                pygame.draw.rect(self.action_surface, self.BUTTON_BG_COLOR, button_rect, border_radius=self.BUTTON_RADIUS)
                self.action_surface.blit(button_surf, button_label)
            screen.blit(self.action_surface, (self.x+self.card_width+10, self.y))

    def pick_action_from_mouse(self, mouse_pos: tuple[int,int]):
        local_pos = (mouse_pos[0]-self.x-self.card_width, mouse_pos[1]-self.y)
        
        for i, (_, _, button_rect) in self.possible_actions:
            if button_rect.collidepoint(local_pos):
                if i == ActionType.ROADBUILD:
                    print("build road")
                elif i == ActionType.TOWNBUILD:
                    print("build town")
                elif i == ActionType.CITYBUILD:
                    print("build city")
                elif i == ActionType.DEVELOPMENT:
                    print("development")
                else:
                    print("trade")

    def set_possible_action(self):
        self.possible_actions = []
        # 街道建設
        if self.resources[ResourceCardType.TREE] >= 1 and self.resources[ResourceCardType.BRICK] >= 1:
            self.possible_actions.append((ActionType.ROADBUILD, self.actions[ActionType.ROADBUILD]))
        # 開拓地建設
        if self.resources[ResourceCardType.TREE] >= 1 and self.resources[ResourceCardType.BRICK] >= 1 and self.resources[ResourceCardType.SHEEP] >= 1 and self.resources[ResourceCardType.WHEAT] >= 1:
            self.possible_actions.append((ActionType.TOWNBUILD, self.actions[ActionType.TOWNBUILD]))
        # 都市化
        if self.resources[ResourceCardType.WHEAT] >= 2 and self.resources[ResourceCardType.ORE] >= 3:
            self.possible_actions.append((ActionType.CITYBUILD, self.actions[ActionType.CITYBUILD]))
        # 発展
        if self.resources[ResourceCardType.SHEEP] >= 1 and self.resources[ResourceCardType.WHEAT] >= 1 and self.resources[ResourceCardType.ORE] >= 1:
            self.possible_actions.append((ActionType.DEVELOPMENT, self.actions[ActionType.DEVELOPMENT]))
        # 交渉
        if sum(self.resources):
            self.possible_actions.append((ActionType.TRADE, self.actions[ActionType.TRADE])) 

        self.crnt_action = "action" if len(self.possible_actions) else "normal"
        

    def add_resources(self, resources_to_add: list[int]):
        self.resources = [i+j for i, j in zip(self.resources, resources_to_add)]

    def count_resources_to_be_discarded(self):
        return sum(self.resources) // 2 if sum(self.resources) >= 8 else 0