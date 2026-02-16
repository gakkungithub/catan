import pygame
import random
import os

class Board:

    # ====== 定数 ======
    VERTEX_DIR = ((0,-2),(2,-1),(2,1),(0,2),(-2,1),(-2,-1))
    SCALEX, SCALEY = 30, 36
    SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720

    LINE_COLOR = (0,0,0)
    BG_COLOR = (0,174,239)
    NUMBER_COLOR = (0,0,0)
    PORT_FONT_COLOR = (0,0,0)
    BRIDGE_COLOR = (80,34,0)

    BRIDGE_THICKNESS = 6

    RESOURCE_COLORS = {
        "tree": (0,85,46),
        "brick": (181,82,51),
        "sheep": (195,216,37),
        "wheat": (255,236,71),
        "ore": (169,169,169),
        "gold": (57,57,58),
        "dessert": (196,153,97),
    }

    PORT_ICON_SHIFTS = (
        (-0.5,-0.5),(-1,0),(-0.5,0.5),
        (0.5,0.5),(1,0),(0.5,-0.5)
    )

    PORT_BRIDGE_SHIFTS = (
        ((-0.6,0),(0,-0.6)),
        ((-0.6,0),(-0.6,0)),
        ((0,0.6),(-0.6,0)),
        ((0,0.6),(0.6,0)),
        ((0.6,0),(0.6,0)),
        ((0.6,0),(0,-0.6))
    )

    # ====== 初期化 ======
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        )

        self.font = pygame.font.SysFont("Arial", 24)
        self.images = {}  # 画像キャッシュ

        self.space_pos = (
            (-4,-6),(0,-6),(4,-6),
            (-6,-3),(-2,-3),(2,-3),(6,-3),
            (-8,0),(-4,0),(0,0),(4,0),(8,0),
            (-6,3),(-2,3),(2,3),(6,3),
            (-4,6),(0,6),(4,6)
        )

        self.resources, self.numbers = self.generate_resources_and_numbers()

        self.ports = {
            ((0,-8),(-2,-7)): ("ore",0),
            ((4,-8),(6,-7)): ("general",5),
            ((-6,-5),(-8,-4)): ("sheep",0),
            ((8,-4),(8,-2)): ("wheat",4),
            ((-10,-1),(-10,1)): ("general",1),
            ((8,2),(8,4)): ("general",4),
            ((-8,4),(-6,5)): ("tree",2),
            ((-2,7),(0,8)): ("brick",2),
            ((6,7),(4,8)): ("general",3),
        }

    # ====== 共通処理 ======
    def to_screen(self, pos):
        """ワールド座標 → 画面座標"""
        return (
            pos[0]*self.SCALEX + self.SCREEN_WIDTH//2,
            pos[1]*self.SCALEY + self.SCREEN_HEIGHT//2
        )

    def get_image(self, name):
        if name not in self.images:
            path = os.path.join("images", f"{name}.png")
            self.images[name] = pygame.image.load(path)
        return self.images[name]

    # ====== 生成 ======
    def generate_resources_and_numbers(self):
        resources = (
            ["brick"]*3 + ["ore"]*3 +
            ["tree"]*4 + ["wheat"]*4 +
            ["sheep"]*4 + ["dessert"]
        )
        random.shuffle(resources)

        numbers = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]
        random.shuffle(numbers)
        numbers.insert(resources.index("dessert"), 0)

        return resources, numbers

    # ====== 描画 ======
    def draw(self):
        self.screen.fill(self.BG_COLOR)

        for i, pos in enumerate(self.space_pos):
            self.draw_hex(i, pos)

        for edge, (name, d) in self.ports.items():
            self.draw_port(edge, name, d)

        pygame.display.flip()

    def draw_hex(self, index, center):
        points = [
            self.to_screen((center[0]+dx, center[1]+dy))
            for dx,dy in self.VERTEX_DIR
        ]

        pygame.draw.polygon(
            self.screen,
            self.RESOURCE_COLORS[self.resources[index]],
            points
        )
        pygame.draw.polygon(self.screen, self.LINE_COLOR, points, 2)

        if self.numbers[index]:
            surf = self.font.render(
                str(self.numbers[index]), True, self.NUMBER_COLOR
            )
            self.screen.blit(surf, surf.get_rect(center=self.to_screen(center)))

    # ====== 港 ======
    def draw_port(self, edge, name, direction):

        mid = (
            (edge[0][0]+edge[1][0])/2,
            (edge[0][1]+edge[1][1])/2
        )

        sx, sy = self.PORT_ICON_SHIFTS[direction]
        icon_pos = self.to_screen((mid[0]+sx, mid[1]+sy))

        if name == "general":
            surf = self.font.render("3:1", True, self.PORT_FONT_COLOR)
            self.screen.blit(surf, surf.get_rect(center=icon_pos))
        else:
            img = self.get_image(name)
            self.screen.blit(img, img.get_rect(center=icon_pos))

        self.draw_bridge(edge, direction)

    def draw_bridge(self, edge, direction):
        shifts = self.PORT_BRIDGE_SHIFTS[direction]

        for p, shift in zip(edge, shifts):
            start = self.to_screen(p)
            end = (
                start[0] + shift[0]*self.SCALEX,
                start[1] + shift[1]*self.SCALEY
            )
            pygame.draw.line(
                self.screen,
                self.BRIDGE_COLOR,
                start, end,
                self.BRIDGE_THICKNESS
            )

