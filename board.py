import pygame
import random
import os
from enum import Enum
from collections import defaultdict
from human import HumanPlayer
import numpy as np
import math
from image_manager import ImageManager
from card import HandCards
from dices import Dices
from card import ResourceCardType, DevelopmentCardType, ActionType

class BoardState(Enum):
    SETFIRSTTOWN = 0
    SETFIRSTROAD = 1
    SETSECONDTOWN = 2
    SETSECONDROAD = 3
    SETTOWN = 4
    SETROAD = 5
    DEVELOPROAD = 6
    SETCITY = 7
    TRADE = 8
    ROLLDICE = 9
    DISCARD = 10
    THIEF = 11
    STEAL = 12
    PLENTY = 13
    MONOPOLY = 14
    ACTION = 15

class Board:
    VERTEX_DIR = ((0,-2),(2,-1),(2,1),(0,2),(-2,1),(-2,-1))
    SCALEX, SCALEY = 30, 36
    SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
    HANDCARD_WIDTH, HANDCARD_HEIGHT = 360, 200
    SPECIALCARD_WIDTH, SPECIALCARD_HEIGHT = 240, 180

    LINE_COLOR = (0,0,0)
    BG_COLOR = (0,174,239)
    NUMBER_COLOR = (0,0,0)
    PORT_FONT_COLOR = (0,0,0)
    BRIDGE_COLOR = (80,34,0)

    CHARA_COLOR_NAME = ("red", "blue", "white", "orange")
    CHARA_COLOR = ((255,0,0),(0,0,255),(255,255,255),(245,130,32))

    BRIDGE_THICKNESS = 6
    VERTEX_RADIUS = 8
    NUMBER_CHIP_RADIUS = 20
    LINE_CLICK_RANGE = 6
    LINE_WIDTH = 2

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

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        )

        self.font = pygame.font.SysFont("Arial", 24)
        self.images: dict[str, pygame.Surface] = {}  # 画像キャッシュ

        self.space_pos = (
            (-4,-6),(0,-6),(4,-6),
            (-6,-3),(-2,-3),(2,-3),(6,-3),
            (-8,0),(-4,0),(0,0),(4,0),(8,0),
            (-6,3),(-2,3),(2,3),(6,3),
            (-4,6),(0,6),(4,6)
        )

        self.resource_by_space, self.number_by_space, self.developments = self.set_cards_and_numbers()
        self.vertex_details, self.edge_details = self.get_board_details()

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

        self.vertex_to_ports: dict[tuple[int,int], str] = {}
        for edge, (resource, _) in self.ports.items():
            self.vertex_to_ports[edge[0]] = resource
            self.vertex_to_ports[edge[1]] = resource

        # これらは後々HumanPlayerに設定すると思われる
        self.ways_already_set: dict[tuple[tuple[int,int], tuple[int,int]], int] = defaultdict(int)
        self.towns_already_set: dict[tuple[int,int], int] = defaultdict(int)
        self.cities_already_set: dict[tuple[int,int], int] = defaultdict(int)

        # 「発見」発展カードで取得する資源を管理するリスト
        self.resources_to_get_by_plenty: list[int] = [0] * 5
        # 今まで取得してきた「資源」カードの取得枚数を格納する
        self.resources_already_get: list[int] = [0] * 5

        self.crnt_state = BoardState.SETFIRSTTOWN

        self.crnt_player_index = 0
        self.player_list: list[HumanPlayer] = [HumanPlayer(i, self.get_first_possible_town_pos()) for i in range(4)]

        # 名前は後で変えられるようにする
        self.hand_cards_by_player: tuple[HandCards] = (HandCards(pygame.Rect(10, 10, self.HANDCARD_WIDTH, self.HANDCARD_HEIGHT), self.CHARA_COLOR[0], "Player 1", self.resources_already_get),
                                                      HandCards(pygame.Rect(self.SCREEN_WIDTH - self.HANDCARD_WIDTH - 10, 10, self.HANDCARD_WIDTH, self.HANDCARD_HEIGHT), self.CHARA_COLOR[1], "Player 2", self.resources_already_get),
                                                      HandCards(pygame.Rect(10, self.SCREEN_HEIGHT - self.HANDCARD_HEIGHT - 10, self.HANDCARD_WIDTH, self.HANDCARD_HEIGHT), self.CHARA_COLOR[2], "Player 3", self.resources_already_get),
                                                      HandCards(pygame.Rect(self.SCREEN_WIDTH - self.HANDCARD_WIDTH - 10, self.SCREEN_HEIGHT - self.HANDCARD_HEIGHT - 10, self.HANDCARD_WIDTH, self.HANDCARD_HEIGHT), self.CHARA_COLOR[3], "Player 4", self.resources_already_get))

        # 交渉を2度行えないように、交渉が成立した時にこの変数をFalseにする
        self.is_trade_not_done: bool = True
        # 2枚目の発展カードを使えないように、発展カードを使った時にこの変数をTrueにする
        self.is_development_used: bool = False
        # 最大騎士力を持っているプレイヤーと、その騎士カードの枚数
        self.max_knight_power_player: tuple[int, int] | None = None
        # 最長経路のプレイヤー
        self.max_length_player: int | None = None

        # サイコロ * 2 のインスタンス
        self.dices = Dices(pygame.Rect(self.SCREEN_WIDTH*5/12,self.SCREEN_HEIGHT*5/12,self.SCREEN_WIDTH*1/6,self.SCREEN_HEIGHT*1/6))

        # 最大騎士力と最長経路の所持者を表示する領域
        self.special_cards_surface = pygame.Surface(
            (self.SPECIALCARD_WIDTH, self.SPECIALCARD_HEIGHT), pygame.SRCALPHA)

        self.max_length_image = ImageManager.load("max_length")
        self.max_knight_power_image = ImageManager.load("max_knight_power")
        self.thief_image = ImageManager.load("thief")
        
    def get_first_possible_town_pos(self):
        """最初に置ける開拓地の場所を取得"""
        possible_town_pos: set[tuple[int,int]] = set()
        for pos in self.space_pos:
            for dx, dy in self.VERTEX_DIR:
                possible_town_pos.add((pos[0]+dx, pos[1]+dy))
        return possible_town_pos

    def to_screen(self, pos: tuple[int,int]):
        """ワールド座標 → 画面座標"""
        return (
            pos[0]*self.SCALEX + self.SCREEN_WIDTH//2,
            pos[1]*self.SCALEY + self.SCREEN_HEIGHT//2
        )

    def set_cards_and_numbers(self):
        """マスの資源と番号の配置を決める"""
        resource_by_space = (
            ["brick"]*3 + ["ore"]*3 +
            ["tree"]*4 + ["wheat"]*4 +
            ["sheep"]*4 + ["dessert"]
        )
        random.shuffle(resource_by_space)

        number_by_space = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]
        random.shuffle(number_by_space)
        self.thief_pos_index = resource_by_space.index("dessert")
        number_by_space.insert(self.thief_pos_index, 0)

        developments = (
            [DevelopmentCardType.KNIGHT]*14 +
            [DevelopmentCardType.ROAD]*2 +
            [DevelopmentCardType.PLENTY]*2 +
            [DevelopmentCardType.MONOPOLY]*2 +
            [DevelopmentCardType.POINT] * 5
        )
        random.shuffle(developments)

        # developmentsはdequeにするかどうか後で決める
        return resource_by_space, number_by_space, developments
    
    def get_board_details(self, isSea: bool = False):
        """頂点と辺の情報を取得する(どのマスに属しているかをインデックスを取得できるようにする)"""
        vertex_details: defaultdict[tuple[int,int], set[int]] = defaultdict(set)
        edge_details: defaultdict[tuple[tuple[int,int], tuple[int,int]], dict[str, bool]] = defaultdict(lambda: {"road": False, "ship": False})
        edge_check_count: defaultdict[tuple[tuple[int,int], tuple[int,int]], int] = defaultdict(int)

        for i in range(len(self.number_by_space)):
            sx, sy = self.space_pos[i]
            for dindex, (dx, dy) in enumerate(self.VERTEX_DIR):
                vertex_details[(sx+dx, sy+dy)].add(i)
                ex, ey = self.VERTEX_DIR[(dindex+1)%6]
                edge: tuple[tuple[int,int], tuple[int,int]] = tuple(sorted(((sx+dx, sy+dy), (sx+ex, sy+ey)), key=lambda x: x[1]))
                if self.resource_by_space[i] == "sea":
                    edge_details[edge]["sea"] = True
                else:
                    edge_details[edge]["road"] = True
                edge_check_count[edge] += 1

        if isSea:
            edge_details = {edge: {"road": edge_details[edge]["road"], "sea": True} if indexes == 1 else edge_details[edge] for edge, indexes in edge_check_count.items()}

        return vertex_details, edge_details
                    
    # 盤面を描画
    def draw(self):
        self.screen.fill(self.BG_COLOR)

        for i, pos in enumerate(self.space_pos):
            self.draw_hex(i, pos)

        for edge, (name, d) in self.ports.items():
            self.draw_port(edge, name, d)

        for edge, player_index in self.ways_already_set.items():
            # この関数についても、プレイヤーによって表示を切り替えられるようにする
            self.draw_road(edge, player_index)

        self.draw_towns_and_cities()

        # 現在の行動が最初の道配置であるならそれに対する表示を行う
        if self.crnt_state in (BoardState.SETFIRSTROAD, BoardState.SETSECONDROAD, BoardState.SETROAD, BoardState.DEVELOPROAD):
            for edge in self.player_list[self.crnt_player_index].possible_road_pos:
                self.draw_possible_road(edge)
            for edge in self.player_list[self.crnt_player_index].possible_ship_pos:
                self.draw_possible_road(edge)

        # サイコロの描画
        if self.crnt_state == BoardState.ROLLDICE:
            # 7が出た場合
            if (dices_result := self.dices.draw(self.screen)) == 7:
                self.crnt_state = BoardState.DISCARD if any([hc.set_resource_num_to_be_discarded() for hc in self.hand_cards_by_player]) else BoardState.THIEF 

            elif dices_result:
                hit_space_pos: list[tuple[int, tuple[int,int]]] = [(i, self.space_pos[i]) for i, n in enumerate(self.number_by_space) if n == dices_result]
                resources_to_be_added_by_player_list = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]

                for space_index, space_pos in hit_space_pos:
                    # ここは関数化するか後で考える
                    for vx, vy in self.VERTEX_DIR:
                        if (player_index := self.towns_already_set.get((space_pos[0]+vx, space_pos[1]+vy))) is not None:
                            resource = self.resource_by_space[space_index]
                            if resource == "tree":
                                resources_to_be_added_by_player_list[player_index][0] += 1
                            elif resource == "brick":
                                resources_to_be_added_by_player_list[player_index][1] += 1
                            elif resource == "sheep":
                                resources_to_be_added_by_player_list[player_index][2] += 1
                            elif resource == "wheat":
                                resources_to_be_added_by_player_list[player_index][3] += 1
                            elif resource == "ore":
                                resources_to_be_added_by_player_list[player_index][4] += 1
                            # 金脈の場合
                            else:
                                pass
                        elif (player_index := self.cities_already_set.get((space_pos[0]+vx, space_pos[1]+vy))) is not None:
                            resource = self.resource_by_space[space_index]
                            if resource == "tree":
                                resources_to_be_added_by_player_list[player_index][0] += 2
                            elif resource == "brick":
                                resources_to_be_added_by_player_list[player_index][1] += 2
                            elif resource == "sheep":
                                resources_to_be_added_by_player_list[player_index][2] += 2
                            elif resource == "wheat":
                                resources_to_be_added_by_player_list[player_index][3] += 2
                            elif resource == "ore":
                                resources_to_be_added_by_player_list[player_index][4] += 2
                            # 金脈の場合
                            else:
                                pass
                
                resources_to_be_added_for_all_players = [sum(values) for values in zip(*resources_to_be_added_by_player_list)]
                resources_cannot_be_added = [
                    self.resources_already_get[i] == 19 or
                    (
                        self.resources_already_get[i] + resources_to_be_added_for_all_players[i] >= 19
                        and sum(resource_to_be_added_by_player[i] > 0 for resource_to_be_added_by_player in resources_to_be_added_by_player_list) >= 2
                    )
                    for i in range(5)
                ]

                for i, cannot in enumerate(resources_cannot_be_added):
                    if cannot:
                        for player in resources_to_be_added_by_player_list:
                            player[i] = 0
                for player_index, resources_to_be_added_by_player in enumerate(resources_to_be_added_by_player_list):
                    self.hand_cards_by_player[player_index].add_resources(resources_to_be_added_by_player)

                self.set_board_state_to_action()

        # 持ち札の描画
        for hand_cards in self.hand_cards_by_player:
            hand_cards.draw(self.screen)

        self.screen.blit(self.special_cards_surface, (self.SCREEN_WIDTH-self.SPECIALCARD_WIDTH-10, (self.SCREEN_HEIGHT-self.SPECIALCARD_HEIGHT)//2))
        self.special_cards_surface.fill((150,150,150))

        self.special_cards_surface.blit(self.max_length_image, self.max_length_image.get_rect(center=(self.SPECIALCARD_WIDTH//4, self.SPECIALCARD_HEIGHT//2)))
        max_length_surf = self.font.render(
            self.hand_cards_by_player[self.max_length_player].player_name if self.max_length_player is not None else "---", True, self.CHARA_COLOR[self.max_length_player] if self.max_length_player is not None else self.LINE_COLOR
        )
        self.special_cards_surface.blit(max_length_surf, max_length_surf.get_rect(center=(self.SPECIALCARD_WIDTH//4, self.SPECIALCARD_HEIGHT//2+60)))
        
        self.special_cards_surface.blit(self.max_knight_power_image, self.max_knight_power_image.get_rect(center=(self.SPECIALCARD_WIDTH*3//4, self.SPECIALCARD_HEIGHT//2)))
        max_knight_power_surf = self.font.render(
            self.hand_cards_by_player[self.max_knight_power_player[0]].player_name if self.max_knight_power_player is not None else "---", True, self.CHARA_COLOR[self.max_knight_power_player[0]] if self.max_knight_power_player is not None else self.LINE_COLOR
        )
        self.special_cards_surface.blit(max_knight_power_surf, max_knight_power_surf.get_rect(center=(self.SPECIALCARD_WIDTH*3//4, self.SPECIALCARD_HEIGHT//2+60)))
        
        pygame.display.flip()

    # 六角形マスの描画
    def draw_hex(self, index, center):
        points = [
            self.to_screen((center[0]+dx, center[1]+dy))
            for dx,dy in self.VERTEX_DIR
        ]
        pygame.draw.polygon(
            self.screen,
            self.RESOURCE_COLORS[self.resource_by_space[index]],
            points
        )
        pygame.draw.polygon(self.screen, self.LINE_COLOR, points, 2)

        if index == self.thief_pos_index:
            self.screen.blit(self.thief_image, self.thief_image.get_rect(center=self.to_screen(center)))
        elif self.number_by_space[index]:
            surf = self.font.render(
                str(self.number_by_space[index]), True, self.NUMBER_COLOR
            )
            self.screen.blit(surf, surf.get_rect(center=self.to_screen(center)))

        # 盗賊を動かす状態ならその場所の候補を描画する
        if self.crnt_state == BoardState.THIEF and index != self.thief_pos_index:
            pygame.draw.circle(self.screen, self.LINE_COLOR, self.to_screen(center), self.NUMBER_CHIP_RADIUS, self.LINE_WIDTH)

    # 開拓地と都市の描画
    def draw_towns_and_cities(self):
        for vertex, player_index in self.towns_already_set.items():
            if player_index == self.crnt_player_index and self.crnt_state == BoardState.SETCITY:
                pygame.draw.circle(self.screen, self.CHARA_COLOR[self.crnt_player_index], self.to_screen(vertex), self.VERTEX_RADIUS)
            else:
                img = ImageManager.load(f"{self.CHARA_COLOR_NAME[player_index]}_town")
                self.screen.blit(img, img.get_rect(center=self.to_screen(vertex)))

        for vertex, player_index in self.cities_already_set.items():
            img = ImageManager.load(f"{self.CHARA_COLOR_NAME[player_index]}_city")
            self.screen.blit(img, img.get_rect(center=self.to_screen(vertex)))

        if self.crnt_state in (BoardState.SETFIRSTTOWN, BoardState.SETSECONDTOWN, BoardState.SETTOWN):
            for vertex in self.player_list[self.crnt_player_index].possible_town_pos:
                pygame.draw.circle(self.screen, self.CHARA_COLOR[self.crnt_player_index], self.to_screen(vertex), self.VERTEX_RADIUS)

    # 道を描画
    def draw_road(self, edge: tuple[tuple[int,int], tuple[int, int]], player_index: int):
        start = self.to_screen(edge[0])
        end = self.to_screen(edge[1])
        pygame.draw.line(
            self.screen,
            self.CHARA_COLOR[player_index],
            start, end,
            self.LINE_CLICK_RANGE * 2
        )

    # 候補道を描画 (中は空白)
    def draw_possible_road(self, edge: tuple[tuple[int,int], tuple[int, int]]):
        start = self.to_screen(edge[0])
        end = self.to_screen(edge[1])
        if start[0] == end[0]:
            points = [(start[0]-self.LINE_CLICK_RANGE, start[1]), (start[0]+self.LINE_CLICK_RANGE, start[1]),
                    (end[0]+self.LINE_CLICK_RANGE, end[1]), (end[0]-self.LINE_CLICK_RANGE, end[1])]
        else:
            points = [(start[0], start[1]-self.LINE_CLICK_RANGE), (start[0], start[1]+self.LINE_CLICK_RANGE),
                    (end[0], end[1]+self.LINE_CLICK_RANGE), (end[0], end[1]-self.LINE_CLICK_RANGE)]
        pygame.draw.polygon(self.screen, self.CHARA_COLOR[self.crnt_player_index], points, self.LINE_CLICK_RANGE)

    # 港を描画
    def draw_port(self, edge, name, direction):

        mid = (
            (edge[0][0]+edge[1][0])/2,
            (edge[0][1]+edge[1][1])/2
        )

        sx, sy = self.PORT_ICON_SHIFTS[direction]

        if name == "general":
            ratio_pos = self.to_screen((mid[0]+sx, mid[1]+sy))
            surf = self.font.render("3:1", True, self.PORT_FONT_COLOR)
            self.screen.blit(surf, surf.get_rect(center=ratio_pos))
        else:
            img = ImageManager.load(name)
            icon_pos = self.to_screen((mid[0]+sx, mid[1]+sy))
            self.screen.blit(img, img.get_rect(center=icon_pos))
            ratio_pos = self.to_screen((mid[0]+sx*2.5, mid[1]+sy*2.5))
            surf = self.font.render("2:1", True, self.PORT_FONT_COLOR)
            self.screen.blit(surf, surf.get_rect(center=ratio_pos))

        self.draw_bridge(edge, direction)

    # 橋を描画
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

    # 道を設置
    def set_road(self, edge: tuple[tuple[int,int], tuple[int,int]], player_index: int):
        self.ways_already_set[edge] = player_index
        self.hand_cards_by_player[player_index].road_count += 1
        for player in self.player_list:
            player.possible_road_pos.discard(edge)

    # 開拓地を設置
    def set_town(self, pos: tuple[int,int]):
        self.delete_possible_town_pos(pos)
        self.hand_cards_by_player[self.crnt_player_index].town_count += 1
        self.towns_already_set[pos] = self.crnt_player_index

    # 都市を設置
    def set_city(self, pos: tuple[int,int]):
        self.hand_cards_by_player[self.crnt_player_index].town_count -= 1
        self.hand_cards_by_player[self.crnt_player_index].city_count += 1
        self.towns_already_set.pop(pos)
        self.cities_already_set[pos] = self.crnt_player_index

    # 開拓地に関するマウスアクションを管理
    def pick_town_pos_from_mouse(self, mouse_pos: tuple[int,int]):
        if self.crnt_state not in (BoardState.SETTOWN, BoardState.SETFIRSTTOWN, BoardState.SETSECONDTOWN):
            return False
        
        mx, my = mouse_pos
        best_pos = None
        best_dist = None
        for town_pos in self.player_list[self.crnt_player_index].possible_town_pos:
            tx, ty = self.to_screen(town_pos)
            dist = math.hypot(mx - tx, my - ty)
            if dist <= self.VERTEX_RADIUS and (best_dist is None or dist < best_dist):
                best_dist = dist
                best_pos = town_pos

        if best_pos is not None:
            if self.crnt_state == BoardState.SETTOWN:
                self.set_town(best_pos)
                self.set_board_state_to_action()
            elif self.crnt_state == BoardState.SETSECONDTOWN:
                self.set_second_town(best_pos)
                resources_to_be_added: list[int] = [0,0,0,0,0]
                for space_index in self.vertex_details[best_pos]:
                    if (resource := self.resource_by_space[space_index]) not in ("dessert", "sea"):
                        if resource == "tree":
                            resources_to_be_added[0] += 1
                        elif resource == "brick":
                            resources_to_be_added[1] += 1
                        elif resource == "sheep":
                            resources_to_be_added[2] += 1
                        elif resource == "wheat":
                            resources_to_be_added[3] += 1
                        elif resource == "ore":
                            resources_to_be_added[4] += 1
                        # 金脈の場合
                        else:
                            pass
                self.hand_cards_by_player[self.crnt_player_index].add_resources(resources_to_be_added)
            else:
                self.set_first_town(best_pos)
            self.get_longest_road()
            return True
        
        return False

    # 都市に関するマウスアクションを管理
    def pick_city_pos_from_mouse(self, mouse_pos: tuple[int,int]):
        if self.crnt_state != BoardState.SETCITY:
            return False
        
        mx, my = mouse_pos
        best_pos = None
        best_dist = None
        for city_pos, player_index in self.towns_already_set.items():
            if player_index != self.crnt_player_index:
                continue

            tx, ty = self.to_screen(city_pos)
            dist = math.hypot(mx - tx, my - ty)
            if dist <= self.VERTEX_RADIUS and (best_dist is None or dist < best_dist):
                best_dist = dist
                best_pos = city_pos

        if best_pos is not None:
            self.set_city(best_pos)
            self.set_board_state_to_action()
            return True
        
        return False
    
    # 道に関するマウスアクションを管理
    def pick_way_pos_from_mouse(self, mouse_pos: tuple[int,int]):
        if self.crnt_state not in (BoardState.SETROAD, BoardState.SETFIRSTROAD, BoardState.SETSECONDROAD, BoardState.DEVELOPROAD):
            return False
        
        best_edge = None
        best_dist = None
        for road_edge in self.player_list[self.crnt_player_index].possible_road_pos:
            from_vertex, to_vertex = road_edge
            fvertex = np.array(self.to_screen(from_vertex))
            tvertex = np.array(self.to_screen(to_vertex))
            mpos = np.array(mouse_pos)

            u = tvertex - fvertex
            v = mpos - fvertex

            uu = np.dot(u, u)

            # 垂線の位置
            t = np.dot(v, u) / uu

            if 0 <= t <= 1:
                # 距離（外積）
                dist: float = abs(np.cross(u, v)) / np.linalg.norm(u)
                if dist <= self.LINE_CLICK_RANGE and (best_dist is None or dist < best_dist):
                    best_dist = dist
                    best_edge = road_edge
        
        if best_edge is not None:
            self.set_road(best_edge, self.crnt_player_index)
            self.update_possible_ways_from_vertex(best_edge[0], "road")
            self.update_possible_ways_from_vertex(best_edge[1], "road")
            if self.crnt_state == BoardState.SETFIRSTROAD:
                if self.crnt_player_index == 3:
                    self.crnt_state = BoardState.SETSECONDTOWN
                else:
                    self.crnt_state = BoardState.SETFIRSTTOWN
                    self.crnt_player_index += 1 
            elif self.crnt_state == BoardState.SETSECONDROAD:
                self.player_list[self.crnt_player_index].possible_town_pos = set()
                self.update_possible_town_pos(best_edge[0])
                self.update_possible_town_pos(best_edge[1])
                if self.crnt_player_index == 0:
                    self.crnt_state = BoardState.ROLLDICE
                else:
                    self.crnt_state = BoardState.SETSECONDTOWN
                    self.crnt_player_index -= 1
            elif self.crnt_state == BoardState.SETROAD:
                self.update_possible_town_pos(best_edge[0])
                self.update_possible_town_pos(best_edge[1])
                self.set_board_state_to_action()
            elif self.crnt_state == BoardState.DEVELOPROAD:
                self.update_possible_town_pos(best_edge[0])
                self.update_possible_town_pos(best_edge[1])
                # 2つ目の道を作れない場合はそこで街道建設を終了する
                if len(self.player_list[self.crnt_player_index].possible_road_pos) + len(self.player_list[self.crnt_player_index].possible_ship_pos) == 0:
                    self.set_board_state_to_action()
                self.crnt_state = BoardState.SETROAD
            self.get_longest_road()
            return True
        
        return False

    # 盗賊の移動に関するマウスアクションを管理
    def pick_thief_pos_from_mouse(self, mouse_pos: tuple[int,int]):
        if self.crnt_state != BoardState.THIEF:
            return False
        
        mx, my = mouse_pos
        thief_pos_index = None
        best_dist = None

        for i, space_pos in enumerate(self.space_pos):
            if i == self.thief_pos_index:
                continue
            tx, ty = self.to_screen(space_pos)
            dist = math.hypot(mx - tx, my - ty)
            if dist <= self.NUMBER_CHIP_RADIUS and (best_dist is None or dist < best_dist):
                best_dist = dist
                thief_pos_index = i

        if thief_pos_index is not None:
            if self.crnt_state == BoardState.THIEF:
                self.thief_pos_index = thief_pos_index

                sx, sy = self.space_pos[thief_pos_index]
                is_steal = False
                for dx, dy in self.VERTEX_DIR:
                    if (player_index := self.towns_already_set.get((sx+dx, sy+dy))) not in (None, self.crnt_player_index):
                        self.hand_cards_by_player[player_index].crnt_action = "stolen"
                        is_steal = True
                    elif (player_index := self.cities_already_set.get((sx+dx, sy+dy))) not in (None, self.crnt_player_index):
                        self.hand_cards_by_player[player_index].crnt_action = "stolen"
                        is_steal = True

                if is_steal:
                    self.crnt_state = BoardState.STEAL
                else:
                    self.set_board_state_to_action()
                return True
        
        return False

    # プレイヤーカード(アクションと発展カード)に対するマウスアクションを管理
    def pick_action_in_card_from_mouse(self, mouse_pos: tuple[int,int]):
        if self.crnt_state == BoardState.DISCARD:
            for i, hand_card in enumerate(self.hand_cards_by_player):
                if hand_card.change_resource_num_to_be_discarded(mouse_pos):
                    break
            # 全てのプレイヤーが資源を捨て終わったら盗賊の移動に移る
            if all([hc.resource_num_to_be_discarded == 0 for hc in self.hand_cards_by_player]):
                self.crnt_state = BoardState.THIEF
        elif self.crnt_state == BoardState.STEAL:
            for i, hand_card in enumerate(self.hand_cards_by_player):
                if i == self.crnt_player_index:
                    continue
                if (picked_resource := hand_card.pick_resource_to_steal_from_mouse(mouse_pos)) is None:
                    continue
                self.hand_cards_by_player[self.crnt_player_index].resources[picked_resource] += 1
                for i, hand_card in enumerate(self.hand_cards_by_player):
                    hand_card.crnt_action = "normal"
                self.set_board_state_to_action()
                break
        elif self.crnt_state == BoardState.PLENTY:
            if (resource_to_get := self.hand_cards_by_player[self.crnt_player_index].pick_resource_to_get_from_mouse(mouse_pos)) is None:
                return
            self.resources_to_get_by_plenty[resource_to_get] += 1
            if sum(self.resources_to_get_by_plenty) == 2:
                self.resources_to_get_by_plenty = [min(19-self.resources_already_get[i], self.resources_to_get_by_plenty[i]) for i in range(5)]
                self.hand_cards_by_player[self.crnt_player_index].add_resources(self.resources_to_get_by_plenty)
                self.resources_to_get_by_plenty = [0] * 5
                self.set_board_state_to_action()
        elif self.crnt_state == BoardState.MONOPOLY:
            if (resource_to_get := self.hand_cards_by_player[self.crnt_player_index].pick_resource_to_get_from_mouse(mouse_pos)) is None:
                return
            resource_count = 0
            for i, hand_card in enumerate(self.hand_cards_by_player):
                if i == self.crnt_player_index:
                    continue
                resource_count += hand_card.resources[resource_to_get]
                hand_card.resources[resource_to_get] = 0
            self.hand_cards_by_player[self.crnt_player_index].resources[resource_to_get] += resource_count
            self.set_board_state_to_action()
        elif self.crnt_state == BoardState.TRADE:
            crnt_hand_card = self.hand_cards_by_player[self.crnt_player_index]
            crnt_hand_card.change_resource_num_for_trade(mouse_pos)
            if crnt_hand_card.crnt_action == "normal":
                # 交渉相手は今のところランダムなプレイヤーから選ぶようにしている
                player_index_who_can_agree_with_the_trade: list[int] = []
                for i, hand_card in enumerate(self.hand_cards_by_player):
                    if i == self.crnt_player_index:
                        continue
                    if all([hand_card.resources[i] >= crnt_hand_card.resources_to_be_taken[i] for i in range(5)]):
                        player_index_who_can_agree_with_the_trade.append(i)
                if len(player_index_who_can_agree_with_the_trade):
                    player_agreed_with_trade = random.choice(player_index_who_can_agree_with_the_trade)
                    hand_card.resources = [hand_card.resources[i] + hand_card.resources_to_be_taken[i] - hand_card.resources_to_be_discarded[i] for i in range(5)]
                    self.hand_cards_by_player[player_agreed_with_trade].resources = [self.hand_cards_by_player[player_agreed_with_trade].resources[i] - hand_card.resources_to_be_taken[i] for i in range(5)]
                    self.is_trade_not_done = False
                hand_card.resources_to_be_discarded = [0] * 5
                hand_card.resources_to_be_taken = [0] * 5
                self.set_board_state_to_action()
        elif self.crnt_state == BoardState.ACTION:
            if (action_type := self.hand_cards_by_player[self.crnt_player_index].pick_action_from_mouse(mouse_pos)) is not None:
                if action_type == ActionType.SETROAD:
                    self.crnt_state = BoardState.SETROAD
                elif action_type == ActionType.SETTOWN:
                    self.crnt_state = BoardState.SETTOWN
                elif action_type == ActionType.SETCITY:
                    self.crnt_state = BoardState.SETCITY
                elif action_type == ActionType.DEVELOPMENT:
                    new_development = self.developments.pop(0)
                    self.hand_cards_by_player[self.crnt_player_index].developments_got_now[new_development] += 1
                    self.set_board_state_to_action()
                elif action_type == ActionType.TRADE:
                    self.crnt_state = BoardState.TRADE
                elif action_type == ActionType.QUIT:
                    self.is_development_used = False
                    self.is_trade_not_done = True
                    self.crnt_player_index = (self.crnt_player_index + 1) % 4
                    self.crnt_state = BoardState.ROLLDICE

            if action_type is not None or self.is_development_used:
                return
            
            if (development_type := self.hand_cards_by_player[self.crnt_player_index].pick_development_from_mouse(mouse_pos)) is not None:
                if development_type == DevelopmentCardType.KNIGHT:
                    crnt_knight_power = self.hand_cards_by_player[self.crnt_player_index].developments_used[DevelopmentCardType.KNIGHT]
                    if self.max_knight_power_player is not None:
                        if crnt_knight_power > self.max_knight_power_player[1]:
                            self.hand_cards_by_player[self.crnt_player_index].is_max_knight_power = True
                            self.hand_cards_by_player[self.max_knight_power_player[0]].is_max_knight_power = False
                            self.max_knight_power_player = (self.crnt_player_index, crnt_knight_power)
                    elif crnt_knight_power == 3:
                        self.hand_cards_by_player[self.crnt_player_index].is_max_knight_power = True
                        self.max_knight_power_player = (self.crnt_player_index, crnt_knight_power)
                    self.crnt_state = BoardState.THIEF
                elif development_type == DevelopmentCardType.ROAD:
                    # 使っても道を配置できない状況なら無効となる
                    if len(self.player_list[self.crnt_player_index].possible_road_pos) + len(self.player_list[self.crnt_player_index].possible_ship_pos):
                        self.crnt_state = BoardState.DEVELOPROAD
                    else:
                        self.set_board_state_to_action()
                elif development_type == DevelopmentCardType.PLENTY:
                    self.crnt_state = BoardState.PLENTY
                # development_type == DevelopmentCardType.MONOPOLY
                else:
                    self.crnt_state = BoardState.MONOPOLY

                self.is_development_used = True
            
    def start_dice_rolling(self, mouse_pos: tuple[int,int]):
        if self.crnt_state != BoardState.ROLLDICE:
            return
        
        self.dices.start_dice_rolling(mouse_pos)

    def delete_possible_town_pos(self, vertex: tuple[int,int]):
        # この頂点からはY字状に辺が伸びている
        if vertex[1] % 3 == 2:
            town_pos_cannot_put: set[tuple[int,int]] = {vertex,(vertex[0]-2, vertex[1]-1),(vertex[0], vertex[1]+2),(vertex[0]+2, vertex[1]-1)}
        # この頂点からは上下逆さのY字状に辺が伸びている
        elif vertex[1] % 3 == 1:
            town_pos_cannot_put: set[tuple[int,int]] = {vertex,(vertex[0]-2, vertex[1]+1),(vertex[0], vertex[1]-2),(vertex[0]+2, vertex[1]+1)}
        # 念の為
        else:
            return
        
        for player in self.player_list:
            if player.player_index != self.crnt_player_index:
                for vertex_adjacent in town_pos_cannot_put:
                    if (edge := tuple(sorted((vertex, vertex_adjacent), key=lambda x: x[1]))) in self.ways_already_set:
                        continue
                    if edge in player.possible_road_pos:
                        if not any(vertex_adjacent == e[0] or vertex_adjacent == e[1] for e in self.ways_already_set.keys()):
                            player.possible_road_pos.remove(edge)
                
            player.possible_town_pos.difference_update(town_pos_cannot_put)

    def set_first_town(self, best_pos: tuple[int,int]):
        self.set_town(best_pos)
        self.update_possible_ways_from_vertex(best_pos, "town")
        self.crnt_state = BoardState.SETFIRSTROAD

    def set_second_town(self, best_pos: tuple[int,int]):
        self.set_town(best_pos)
        self.update_possible_ways_from_vertex(best_pos, "town")
        self.crnt_state = BoardState.SETSECONDROAD

    def update_possible_town_pos(self, vertex: tuple[int,int]):
        """現在設置した道に含まれる座標について、その座標と隣り合う座標全てで開拓地または都市がないなら、開拓地を置ける場所候補として登録する"""
        if vertex in self.towns_already_set:
            return
        
        # この頂点からはY字状に辺が伸びている
        if vertex[1] % 3 == 2:
            if ((vertex[0]-2, vertex[1]-1) in self.towns_already_set or
                (vertex[0], vertex[1]+2) in self.towns_already_set or
                (vertex[0]+2, vertex[1]-1) in self.towns_already_set):
                return
        # この頂点からは上下逆さのY字状に辺が伸びている
        elif vertex[1] % 3 == 1:
            if ((vertex[0]-2, vertex[1]+1) in self.towns_already_set or
                (vertex[0], vertex[1]+2) in self.towns_already_set or
                (vertex[0]+2, vertex[1]+1) in self.towns_already_set):
                return
        else:
            return
        
        self.player_list[self.crnt_player_index].possible_town_pos.add(vertex)

    def update_possible_ways_from_vertex(self, vertex: tuple[int,int], object_type: str):
        """現在設置した道または開拓地から道を伸ばせる辺を新たに取得する"""
        # この頂点からはY字状に辺が伸びている
        if vertex[1] % 3 == 2:
            # まずは左上の頂点との辺を確認
            self.update_possible_edge(vertex, (vertex[0]-2, vertex[1]-1), object_type)
            # 次は下の頂点との辺を確認
            self.update_possible_edge(vertex, (vertex[0], vertex[1]+2), object_type)
            # 最後は右上の頂点との辺を確認
            self.update_possible_edge(vertex, (vertex[0]+2, vertex[1]-1), object_type)

        # この頂点からは上下逆さのY字状に辺が伸びている
        elif vertex[1] % 3 == 1:
            # まずは左下の頂点との辺を確認
            self.update_possible_edge(vertex, (vertex[0]-2, vertex[1]+1), object_type)
            # 次は上の頂点との辺を確認
            self.update_possible_edge(vertex, (vertex[0], vertex[1]-2), object_type)
            # 最後は右下の頂点との辺を確認
            self.update_possible_edge(vertex, (vertex[0]+2, vertex[1]+1), object_type)

    def update_possible_edge(self, start_vertex: tuple[int,int], end_vertex: tuple[int,int], object_type: str):
        # この辺が存在しており、まだそこに道が置かれていないかを見る(後々、海賊で規制されていないかも確認できるようにする)
        edge = tuple(sorted((start_vertex, end_vertex), key=lambda x: x[1]))
        if edge in self.edge_details and edge not in self.ways_already_set:
            # 道が置ける辺であり、先端に自分以外の開拓地がない、前置いたのが船ではない場合は道を置ける
            if self.edge_details[edge]["road"] and self.towns_already_set.get(start_vertex) in (None, self.player_list[self.crnt_player_index].player_index) and object_type != "ship":
                self.player_list[self.crnt_player_index].possible_road_pos.add(edge)
            
            # 船が置ける辺であり、先端に自分以外の開拓地がない、前置いたのが道ではない場合は船を置ける
            if self.edge_details[edge]["ship"] and self.towns_already_set.get(start_vertex) in (None, self.player_list[self.crnt_player_index].player_index) and object_type != "town":
                self.player_list[self.crnt_player_index].possible_ship_pos.add(edge)

    def set_board_state_to_action(self):
        self.crnt_state = BoardState.ACTION
        self.hand_cards_by_player[self.crnt_player_index].set_possible_action(
            len(self.player_list[self.crnt_player_index].possible_road_pos) != 0, 
            len(self.player_list[self.crnt_player_index].possible_ship_pos) != 0,
            len(self.player_list[self.crnt_player_index].possible_town_pos) != 0, 
            len(self.developments) != 0,
            self.is_trade_not_done
            )
        
    def get_longest_road(self):
        vertices_list: list[set[tuple[int,int]]] = [set() for _ in range(4)]
        ways_list: list[set[tuple[tuple[int,int],tuple[int,int]]]] = [set() for _ in range(4)]
        for edge, player_index in self.ways_already_set.items():
            v1, v2 = edge
            ways_list[player_index].add(edge)
            vertices_list[player_index].add(v1)
            vertices_list[player_index].add(v2)

        max_length_list = [0] * 4
        for player_index, vertices in enumerate(vertices_list):
            for v in vertices:
                length = self.longest_path_from(v, ways_list[player_index], set(), player_index)
                max_length_list[player_index] = max(max_length_list[player_index], length)

        max_length = max(max_length_list)
        if max_length < 5:
            if self.max_length_player is not None:
                self.hand_cards_by_player[self.max_length_player].is_max_length = False
                self.max_length_player = None
            return
        
        max_length_player_index = [i for i, l in enumerate(max_length_list) if l == max_length]
        if self.max_length_player is None:
            self.max_length_player = self.crnt_player_index
            self.hand_cards_by_player[self.max_length_player].is_max_length = True
        elif self.max_length_player not in max_length_player_index:
            self.hand_cards_by_player[self.max_length_player].is_max_length = False
            self.max_length_player = self.crnt_player_index
            self.hand_cards_by_player[self.max_length_player].is_max_length = True
            
    def longest_path_from(self, vertex: tuple[int,int], ways: set[tuple[tuple[int,int],tuple[int,int]]], visited_edges: set[tuple[tuple[int,int],tuple[int,int]]], player_index: int):
        max_length = 0
        
        for edge in ways:
            if edge not in visited_edges and vertex in edge:
                next_vertex = edge[1] if edge[0] == vertex else edge[0]
                if (self.towns_already_set.get(next_vertex) in (None, player_index)
                    or self.cities_already_set.get(next_vertex) in (None, player_index)):
                    length = 1 + self.longest_path_from(
                        next_vertex,
                        ways,
                        visited_edges | {edge},
                        player_index
                    )
                else:
                    length = 1
                max_length = max(max_length, length)

        return max_length

