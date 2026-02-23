from enum import IntEnum
import pygame
from image_manager import ImageManager
import random

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
    SETROAD = 0
    SETTOWN = 1
    SETCITY = 2
    DEVELOPMENT = 3
    TRADE = 4
    QUIT = 5

class HandCards:
    FONT_SIZE = 24
    BUTTON_FONT_SIZE = 8
    BUTTON_BG_COLOR = (100,100,100)
    BUTTON_RADIUS = 5

    def __init__(self, rect: pygame.Rect, color: tuple[int,int,int], player_name: str):
        self.font = pygame.font.SysFont("Arial", self.FONT_SIZE)
        self.button_font = pygame.font.SysFont("Arial", self.BUTTON_FONT_SIZE)

        self.player_name = player_name
        self.resources = [0] * 5
        self.resources_to_be_discarded = [0] * 5
        self.resources_to_be_taken = [0] * 5
        self.developments = [0] * 5
        self.developments_got_now = [0] * 5
        self.developments_used = [0] * 5

        self.is_max_kinght_power = False

        self.town_count = 0
        self.city_count = 0
        
        self.x = rect[0]
        self.y = rect[1]
        self.card_width = rect[2]-110
        self.height = rect[3]

        self.card_surface = pygame.Surface(
            (rect[2]-110, rect[3]), pygame.SRCALPHA)
        
        self.action_surface = pygame.Surface(
            (100, rect[3]), pygame.SRCALPHA)

        self.color = color

        self.actions = (self.get_button_rect("NEW ROAD", (50,15)), self.get_button_rect("NEW TOWN", (50,15+self.BUTTON_FONT_SIZE+25)), self.get_button_rect("NEW CITY", (50,15+(self.BUTTON_FONT_SIZE+25)*2)),
                        self.get_button_rect("DEVELOPMENT", (50,15+(self.BUTTON_FONT_SIZE+25)*3)), self.get_button_rect("TRADE", (50,15+(self.BUTTON_FONT_SIZE+25)*4)), self.get_button_rect("QUIT", (50,15+(self.BUTTON_FONT_SIZE+25)*5)))
        self.possible_actions: list[tuple[int, tuple[pygame.Surface, pygame.Rect, pygame.Rect]]] = []

        self.arrow_up_image = ImageManager.load("arrow")
        self.arrow_down_image = pygame.transform.rotate(self.arrow_up_image, 180)
        self.arrow_buttons: tuple[tuple[pygame.Rect, pygame.Rect]] = tuple([(self.arrow_up_image.get_rect(topright=(50*(i+1)-2, 75)), self.arrow_down_image.get_rect(topright=(50*(i+1)-2, 95))) for i in range(5)])
        self.possible_arrow_buttons: list[tuple[int, tuple[pygame.Rect, pygame.Rect]]] = []
        self.resource_card_in_out_rect = pygame.Rect(0, 35, self.card_width, 90)

        self.resource_num_to_be_discarded: int = 0
        
        self.resource_images = tuple([self.get_image_rect(name, (10+50*i, 40)) for i, name in enumerate(("tree", "brick", "sheep", "wheat", "ore"))])
        
        self.development_images = tuple([self.get_image_rect(name, (10+50*i, 130)) for i, name in enumerate(("knight", "road", "plenty", "monopoly", "point"))])

        self.crnt_action = "normal"

    def get_button_rect(self, name: str, pos: tuple[int,int]):
        surf = self.button_font.render(name, True, self.color)
        rect = surf.get_rect()
        button_rect = rect.inflate(10*2,7*2)
        button_rect.center = pos
        rect.center = button_rect.center
        return surf, rect, button_rect

    def get_image_rect(self, name: str, pos: tuple[int,int]):
        img = ImageManager.load(name)
        rect = img.get_rect(topleft=pos)
        return img, rect

    def draw(self, screen: pygame.Surface):
        self.card_surface.fill((150,150,150))
        
        surf = self.font.render(self.player_name, True, self.color)
        self.card_surface.blit(surf, surf.get_rect(topleft=(10, 10)))

        # 現在の得点の表示
        surf = self.font.render(f"{self.town_count + self.city_count * 2 + self.developments[4] + self.is_max_kinght_power * 2} / 10", True, self.color)
        self.card_surface.blit(surf, surf.get_rect(topright=(self.card_width-10, 10)))

        # 資源カードの表示
        for i in range(5):
            img, rect = self.resource_images[i]
            self.card_surface.blit(img, rect)
            if self.resource_num_to_be_discarded or self.crnt_action == "give":
                surf = self.font.render(str(self.resources[i] - self.resources_to_be_discarded[i]), True, self.color)
            elif self.crnt_action == "take":
                surf = self.font.render(str(self.resources_to_be_taken[i]), True, self.color)
            else:
                surf = self.font.render(str(self.resources[i]), True, self.color)
            
            self.card_surface.blit(surf, surf.get_rect(topright=(28+50*i, 80)))

        if self.resource_num_to_be_discarded or self.crnt_action == "give":
            for _, (arrow_up_rect, arrow_down_rect) in self.possible_arrow_buttons:
                self.card_surface.blit(self.arrow_up_image, arrow_up_rect)
                self.card_surface.blit(self.arrow_down_image, arrow_down_rect)
        elif self.crnt_action == "take":
            surf = self.button_font.render("by", True, self.color)
            self.card_surface.blit(surf, surf.get_rect(center=(10, 110)))
            for i, (arrow_up_rect, arrow_down_rect) in enumerate(self.arrow_buttons):
                surf = self.button_font.render(str(self.resources_to_be_discarded[i]), True, self.color)
                self.card_surface.blit(surf, surf.get_rect(topright=(28+50*i, 110)))
                self.card_surface.blit(self.arrow_up_image, arrow_up_rect)
                self.card_surface.blit(self.arrow_down_image, arrow_down_rect)

        # 発展カードの表示
        for i in range(5):
            img, rect = self.development_images[i]
            self.card_surface.blit(img, rect)
            surf = self.font.render(str(self.developments[i]), True, self.color)
            self.card_surface.blit(surf, surf.get_rect(topright=(28+50*i, 170)))
            if self.developments_got_now[i]:
                surf = self.button_font.render(f"+{self.developments_got_now[i]}", True, self.color)
                self.card_surface.blit(surf, surf.get_rect(center=(40+50*i, 170)))
            if self.developments_used[i]:
                surf = self.button_font.render(str(self.developments_used[i]), True, self.color)
                self.card_surface.blit(surf, surf.get_rect(center=(40+50*i, 190)))
                if i == DevelopmentCardType.KNIGHT and self.is_max_kinght_power:
                    pygame.draw.circle(self.card_surface, self.color, (40+50*i, 190), 8, 2)

        if self.crnt_action == "action":
            self.action_surface.fill((255,255,255))
            for _, (button_surf, button_label, button_rect) in self.possible_actions:
                pygame.draw.rect(self.action_surface, self.BUTTON_BG_COLOR, button_rect, border_radius=self.BUTTON_RADIUS)
                self.action_surface.blit(button_surf, button_label)
            screen.blit(self.action_surface, (self.x+self.card_width+10, self.y))
        elif self.crnt_action == "stolen":
            pygame.draw.rect(self.card_surface, self.color, self.resource_card_in_out_rect, 2)
            surf = self.font.render("steal ?", True, self.color)
            rect = surf.get_rect(center=(self.card_width // 2, 25))
            pygame.draw.rect(self.card_surface, self.BUTTON_BG_COLOR, rect, border_radius=self.BUTTON_RADIUS)
            self.card_surface.blit(surf, rect)
        elif self.crnt_action == "give":
            pygame.draw.rect(self.card_surface, self.color, self.resource_card_in_out_rect, 2)
            if sum(self.resources_to_be_discarded):
                surf = self.font.render("give", True, self.color)
            else:
                surf = self.font.render("pick any", True, (*self.color, 80))
            rect = surf.get_rect(center=(self.card_width // 2, 25))
            pygame.draw.rect(self.card_surface, self.BUTTON_BG_COLOR, rect, border_radius=self.BUTTON_RADIUS)
            self.card_surface.blit(surf, rect)
        elif self.crnt_action == "take":
            pygame.draw.rect(self.card_surface, self.color, self.resource_card_in_out_rect, 2)
            if sum(self.resources_to_be_taken):
                surf = self.font.render("take", True, self.color)
            else:
                surf = self.font.render("pick any", True, (*self.color, 80))
            rect = surf.get_rect(center=(self.card_width // 2, 25))
            pygame.draw.rect(self.card_surface, self.BUTTON_BG_COLOR, rect, border_radius=self.BUTTON_RADIUS)
            self.card_surface.blit(surf, rect)
        elif self.resource_num_to_be_discarded:
            pygame.draw.rect(self.card_surface, self.color, self.resource_card_in_out_rect, 2)
            # 現在選んだ資源カードの枚数が捨てる枚数と一致していないなら確定ボタンの色を薄くする
            if sum(self.resources_to_be_discarded) == self.resource_num_to_be_discarded:
                surf = self.font.render(f"Finish", True, self.color)
            else:
                surf = self.font.render(f"{sum(self.resources_to_be_discarded)} / {self.resource_num_to_be_discarded}", True, (*self.color, 80))
            rect = surf.get_rect(center=(self.card_width // 2, 25))
            pygame.draw.rect(self.card_surface, self.BUTTON_BG_COLOR, rect, border_radius=self.BUTTON_RADIUS)
            self.card_surface.blit(surf, rect)

        screen.blit(self.card_surface, (self.x, self.y))

    def pick_action_from_mouse(self, mouse_pos: tuple[int,int]):
        local_pos = (mouse_pos[0]-self.x-self.card_width, mouse_pos[1]-self.y)

        for i, (_, _, button_rect) in self.possible_actions:
            if button_rect.collidepoint(local_pos):
                if i == ActionType.SETROAD:
                    self.resources[ResourceCardType.TREE] -= 1
                    self.resources[ResourceCardType.BRICK] -= 1
                elif i == ActionType.SETTOWN:
                    self.resources[ResourceCardType.TREE] -= 1
                    self.resources[ResourceCardType.BRICK] -= 1
                    self.resources[ResourceCardType.SHEEP] -= 1
                    self.resources[ResourceCardType.WHEAT] -= 1
                    number_town_possible_to_set -= 1
                elif i == ActionType.SETCITY:
                    self.resources[ResourceCardType.WHEAT] -= 2
                    self.resources[ResourceCardType.ORE] -= 3
                elif i == ActionType.DEVELOPMENT:
                    self.resources[ResourceCardType.SHEEP] -= 1
                    self.resources[ResourceCardType.WHEAT] -= 1
                    self.resources[ResourceCardType.ORE] -= 1
                elif i == ActionType.TRADE:
                    self.crnt_action = "give"
                    self.get_arrow_buttons()
                    return i
                else:
                    print("quit")
                    # このターンで発展カードを取得した場合、手札に加える
                    if sum(self.developments_got_now):
                        self.developments = [self.developments[i] + self.developments_got_now[i] for i in range(5)]
                        self.developments_got_now = [0] * 5
                self.crnt_action = "normal"
                return i
        
        return None

    def pick_development_from_mouse(self, mouse_pos: tuple[int,int]):
        local_pos = (mouse_pos[0]-self.x, mouse_pos[1]-self.y)

        for i, (_, rect) in enumerate(self.development_images):
            if i == 4 or self.developments[i] == 0:
                continue
            if rect.collidepoint(local_pos):
                self.developments[i] -= 1
                self.developments_used[i] += 1
                self.crnt_action = "normal"
                return i
        
        return None

    def change_resource_num_to_be_discarded(self, mouse_pos: tuple[int,int]):
        if self.resource_num_to_be_discarded == 0:
            return False
        
        local_pos = (mouse_pos[0]-self.x, mouse_pos[1]-self.y)

        if (self.card_width //2 - self.FONT_SIZE * 4.5 <= local_pos[0] <= self.card_width // 2 + self.FONT_SIZE * 4.5 
            and 25 - self.FONT_SIZE // 2 <= local_pos[1] <= 25 + self.FONT_SIZE // 2
            and sum(self.resources_to_be_discarded) == self.resource_num_to_be_discarded):
            self.resources = [self.resources[i] - self.resources_to_be_discarded[i] for i in range(5)]
            self.resources_to_be_discarded = [0] * 5
            self.resource_num_to_be_discarded = 0
            return True
        
        for i, (arrow_up_button, arrow_down_button) in self.possible_arrow_buttons:
            if arrow_up_button.collidepoint(local_pos) and self.resources_to_be_discarded[i] > 0:
                self.resources_to_be_discarded[i] -= 1
                return True
            elif arrow_down_button.collidepoint(local_pos) and sum(self.resources_to_be_discarded) < self.resource_num_to_be_discarded and self.resources_to_be_discarded[i] < self.resources[i]:
                self.resources_to_be_discarded[i] += 1
                return True
        
        return False
    
    def pick_resource_to_steal_from_mouse(self, mouse_pos: tuple[int,int]):
        local_pos = (mouse_pos[0]-self.x, mouse_pos[1]-self.y)

        if self.crnt_action == "stolen" and self.card_width // 2 - self.FONT_SIZE * 3.5 <= local_pos[0] <= self.card_width // 2 + self.FONT_SIZE * 3.5 and 25 - self.FONT_SIZE // 2 <= local_pos[1] <= 25 + self.FONT_SIZE // 2:
            resources_not_zero = [i for i, num in enumerate(self.resources) if num != 0]
            if len(resources_not_zero) == 0:
                return None
            picked_resource = random.choice(resources_not_zero)
            self.resources[picked_resource] -= 1
            return picked_resource
        
        return None

    def pick_resource_to_get_from_mouse(self, mouse_pos: tuple[int,int]):
        local_pos = (mouse_pos[0]-self.x, mouse_pos[1]-self.y)

        for i, (_, rect) in enumerate(self.resource_images):
            if rect.collidepoint(local_pos):
                return i
        
        return None

    def change_resource_num_for_trade(self, mouse_pos: tuple[int,int]):
        if self.crnt_action not in ("give", "take"):
            return False
        
        local_pos = (mouse_pos[0]-self.x, mouse_pos[1]-self.y)

        if (self.card_width //2 - self.FONT_SIZE * 4.5 <= local_pos[0] <= self.card_width // 2 + self.FONT_SIZE * 4.5 
            and 25 - self.FONT_SIZE // 2 <= local_pos[1] <= 25 + self.FONT_SIZE // 2):
            if self.crnt_action == "give" and sum(self.resources_to_be_discarded):
                self.crnt_action = "take"
                return True
            elif self.crnt_action == "take" and sum(self.resources_to_be_taken):
                self.crnt_action = "normal"
                return True
            return False
        
        if self.crnt_action == "give":
            for i, (arrow_up_rect, arrow_down_rect) in self.possible_arrow_buttons:
                if arrow_up_rect.collidepoint(local_pos):
                    if self.crnt_action == "give" and self.resources_to_be_discarded[i] > 0:
                        self.resources_to_be_discarded[i] -= 1
                        return True
                elif arrow_down_rect.collidepoint(local_pos):
                    if self.crnt_action == "give" and self.resources_to_be_discarded[i] < self.resources[i]:
                        self.resources_to_be_discarded[i] += 1
                        return True
        else:
            for i, (arrow_up_rect, arrow_down_rect) in enumerate(self.arrow_buttons):
                if arrow_up_rect.collidepoint(local_pos):
                    if self.crnt_action == "take" and self.resources_to_be_taken[i] < 19 - self.resources[i]:
                        self.resources_to_be_taken[i] += 1
                        return True
                elif arrow_down_rect.collidepoint(local_pos):
                    if self.crnt_action == "take" and self.resources_to_be_taken[i] > 0:
                        self.resources_to_be_taken[i] -= 1
                        return True
        
        return False
    
    # 今のところは船建設は考えない
    def set_possible_action(self, is_able_to_set_road: bool, is_able_to_set_ship: bool, is_able_to_set_town: bool, is_able_to_pick_development: bool, is_trade_not_done: bool):
        self.possible_actions = []
        # 街道建設
        if self.resources[ResourceCardType.TREE] >= 1 and self.resources[ResourceCardType.BRICK] >= 1 and is_able_to_set_road:
            self.possible_actions.append((ActionType.SETROAD, self.actions[ActionType.SETROAD]))
        # 開拓地建設
        if self.resources[ResourceCardType.TREE] >= 1 and self.resources[ResourceCardType.BRICK] >= 1 and self.resources[ResourceCardType.SHEEP] >= 1 and self.resources[ResourceCardType.WHEAT] >= 1 and self.town_count != 5 and is_able_to_set_town:
            self.possible_actions.append((ActionType.SETTOWN, self.actions[ActionType.SETTOWN]))
        # 都市化
        if self.resources[ResourceCardType.WHEAT] >= 2 and self.resources[ResourceCardType.ORE] >= 3 and self.town_count >= 1 and self.city_count < 5:
            self.possible_actions.append((ActionType.SETCITY, self.actions[ActionType.SETCITY]))
        # 発展
        if self.resources[ResourceCardType.SHEEP] >= 1 and self.resources[ResourceCardType.WHEAT] >= 1 and self.resources[ResourceCardType.ORE] >= 1 and is_able_to_pick_development:
            self.possible_actions.append((ActionType.DEVELOPMENT, self.actions[ActionType.DEVELOPMENT]))
        # 交渉 (現在何かしらの資源カードを持っているなら実行できる)
        if sum(self.resources) and is_trade_not_done:
            self.possible_actions.append((ActionType.TRADE, self.actions[ActionType.TRADE])) 
        self.possible_actions.append((ActionType.QUIT, self.actions[ActionType.QUIT]))
        self.crnt_action = "action"
        
    def add_resources(self, resources_to_add: list[int]):
        self.resources = [i+j for i, j in zip(self.resources, resources_to_add)]

    def set_resource_num_to_be_discarded(self):
        self.resource_num_to_be_discarded = sum(self.resources) // 2 if sum(self.resources) >= 8 else 0
        if self.resource_num_to_be_discarded:
            self.get_arrow_buttons()
        return self.resource_num_to_be_discarded
    
    def get_arrow_buttons(self):
        self.possible_arrow_buttons = [(i, buttons) for i, buttons in enumerate(self.arrow_buttons) if self.resources[i]]