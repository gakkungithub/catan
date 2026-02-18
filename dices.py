import pygame, random

class Dices:
    TIME_NUMBER_CHANGE = 30
    TIME_NUMBER_DECIDE = 150
    DICE_RED_COLOR = (255,0,0)
    DICE_BLUE_COLOR = (0,0,255)

    def __init__(self, rect: pygame.Rect):
        self.numbers = [1,2,3,4,5,6]
        self.font = pygame.font.SysFont("Arial", 24)
        self.crnt_number_red = 1
        self.crnt_number_blue = 1
        self.rolling = False
        self.stopping = False
        self.x = rect[0]
        self.y = rect[1]
        self.width = rect[2]
        self.height = rect[3]
        self.surface = pygame.Surface(
            (rect[2], rect[3]), pygame.SRCALPHA)
        self.timer = 0
    
    def start_dice_rolling(self, mouse_pos):
        if self.x <= mouse_pos[0] <= self.x + self.width and self.y <= mouse_pos[1] <= self.y + self.height:
            if self.rolling:
                self.rolling = False
                self.stopping = True
            elif not self.stopping:
                self.rolling = True
                self.timer = 0 

    def draw(self, screen: pygame.Surface):
        self.surface.fill((120,120,120))
        # 今サイコロを回しているなら番号を変える
        if self.rolling or self.stopping:
            self.timer += 10
            if self.stopping and self.timer >= self.TIME_NUMBER_DECIDE:
                self.stopping = False
                return self.crnt_number_red + self.crnt_number_blue

            elif self.rolling and self.timer >= self.TIME_NUMBER_CHANGE:
                self.timer = 0
                self.crnt_number_red = random.choice(self.numbers)
                self.crnt_number_blue = random.choice(self.numbers)

        # 赤サイコロの描画
        pygame.draw.rect(self.surface, self.DICE_RED_COLOR, pygame.Rect(10,10,40,40))
        dice_text_red = self.font.render(str(self.crnt_number_red), True, (255,255,255))
        self.surface.blit(dice_text_red, dice_text_red.get_rect(center=(30,self.height//2)))
        
        # 青サイコロの描画
        pygame.draw.rect(self.surface, self.DICE_BLUE_COLOR, pygame.Rect(self.width-50,10,40,40))
        dice_text_blue = self.font.render(str(self.crnt_number_blue), True, (255,255,255))
        self.surface.blit(dice_text_blue, dice_text_blue.get_rect(center=(self.width-30,self.height//2)))

        screen.blit(self.surface, (self.x, self.y))

        return 0