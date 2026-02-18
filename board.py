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

class BoardState(Enum):
    SETFIRSTTOWN = 0
    SETFIRSTROAD = 1
    SETSECONDTOWN = 2
    SETSECONDROAD = 3
    ROLLDICE = 4
    ACTION = 5

class Board:
    VERTEX_DIR = ((0,-2),(2,-1),(2,1),(0,2),(-2,1),(-2,-1))
    SCALEX, SCALEY = 30, 36
    SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
    HANDCARD_WIDTH, HANDCARD_HEIGHT = 250, 200

    LINE_COLOR = (0,0,0)
    BG_COLOR = (0,174,239)
    NUMBER_COLOR = (0,0,0)
    PORT_FONT_COLOR = (0,0,0)
    BRIDGE_COLOR = (80,34,0)

    CHARA_COLOR_NAME = ("red", "blue", "white", "orange")
    CHARA_COLOR = ((255,0,0),(0,0,255),(255,255,255),(245,130,32))

    BRIDGE_THICKNESS = 6
    VERTEX_RADIUS = 8
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

        self.resources, self.numbers = self.generate_resources_and_numbers()
        self.vertex_details, self.edge_details = self.generate_vertex_and_edge_details()

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

        self.crnt_action = BoardState.SETFIRSTTOWN

        self.crnt_player_index = 0

        self.player_list: list[HumanPlayer] = []
        for i in range(4):
            self.player_list.append(HumanPlayer(i, self.get_first_potential_town_pos()))

        # 名前は後で変えられるようにする
        self.hand_cards_by_player: tuple[HandCards] = (HandCards(pygame.Rect(10, 10, self.HANDCARD_WIDTH, self.HANDCARD_HEIGHT), self.CHARA_COLOR[0], "Player 1"),
                                                      HandCards(pygame.Rect(self.SCREEN_WIDTH - self.HANDCARD_WIDTH - 10, 10, self.HANDCARD_WIDTH, self.HANDCARD_HEIGHT), self.CHARA_COLOR[1], "Player 2"),
                                                      HandCards(pygame.Rect(10, self.SCREEN_HEIGHT - self.HANDCARD_HEIGHT - 10, self.HANDCARD_WIDTH, self.HANDCARD_HEIGHT), self.CHARA_COLOR[2], "Player 3"),
                                                      HandCards(pygame.Rect(self.SCREEN_WIDTH - self.HANDCARD_WIDTH - 10, self.SCREEN_HEIGHT - self.HANDCARD_HEIGHT - 10, self.HANDCARD_WIDTH, self.HANDCARD_HEIGHT), self.CHARA_COLOR[3], "Player 4"))

    def get_first_potential_town_pos(self):
        """最初に置ける開拓地の場所を取得"""
        potential_town_pos: set[tuple[int,int]] = set()
        for pos in self.space_pos:
            for dx, dy in self.VERTEX_DIR:
                potential_town_pos.add((pos[0]+dx, pos[1]+dy))
        return potential_town_pos - set(self.towns_already_set.keys())

    def to_screen(self, pos: tuple[int,int]):
        """ワールド座標 → 画面座標"""
        return (
            pos[0]*self.SCALEX + self.SCREEN_WIDTH//2,
            pos[1]*self.SCALEY + self.SCREEN_HEIGHT//2
        )

    def generate_resources_and_numbers(self):
        """マスの資源と番号の配置を決める"""
        resources = (
            ["brick"]*3 + ["ore"]*3 +
            ["tree"]*4 + ["wheat"]*4 +
            ["sheep"]*4 + ["dessert"]
        )
        random.shuffle(resources)

        numbers = [2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12]
        random.shuffle(numbers)
        self.thief_pos_index = resources.index("dessert")
        numbers.insert(self.thief_pos_index, 0)

        return resources, numbers
    
    def generate_vertex_and_edge_details(self, isSea: bool = False):
        """頂点の情報を取得する(どのマスに属しているかをインデックスを取得できるようにする)"""
        vertex_details: defaultdict[tuple[int,int], set[int]] = defaultdict(set)
        edge_details: defaultdict[tuple[tuple[int,int], tuple[int,int]], dict[str, bool]] = defaultdict(lambda: {"road": False, "ship": False})
        edge_check_count: defaultdict[tuple[tuple[int,int], tuple[int,int]], int] = defaultdict(int)

        for i in range(len(self.numbers)):
            sx, sy = self.space_pos[i]
            for dindex, (dx, dy) in enumerate(self.VERTEX_DIR):
                vertex_details[(sx+dx, sy+dy)].add(i)
                ex, ey = self.VERTEX_DIR[(dindex+1)%6]
                edge: tuple[tuple[int,int], tuple[int,int]] = tuple(sorted(((sx+dx, sy+dy), (sx+ex, sy+ey)), key=lambda x: x[1]))
                if self.resources[i] == "sea":
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

        if self.crnt_action in (BoardState.SETFIRSTROAD, BoardState.SETSECONDROAD, BoardState.ACTION):
            for edge in self.player_list[self.crnt_player_index].potential_road_pos:
                self.draw_potential_road(edge)
            for edge in self.player_list[self.crnt_player_index].potential_ship_pos:
                self.draw_potential_road(edge)

        # 持ち札の描画
        for hand_cards in self.hand_cards_by_player:
            hand_cards.draw(self.screen)

        pygame.display.flip()

    # 六角形マスの描画
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

        if index == self.thief_pos_index:
            img = ImageManager.load("thief")
            self.screen.blit(img, img.get_rect(center=self.to_screen(center)))
        elif self.numbers[index]:
            surf = self.font.render(
                str(self.numbers[index]), True, self.NUMBER_COLOR
            )
            self.screen.blit(surf, surf.get_rect(center=self.to_screen(center)))

        for dx,dy in self.VERTEX_DIR:
            vertex: tuple[int,int] = (center[0]+dx, center[1]+dy)
            if (player_index := self.towns_already_set.get(vertex)) is not None:
                # 後々crnt_player_indexによってどの町を表示するかを切り替えられるようにする
                img = ImageManager.load(f"{self.CHARA_COLOR_NAME[player_index]}_town")
                self.screen.blit(img, img.get_rect(center=self.to_screen(vertex)))
            # 開拓地を置く場所の候補
            elif self.crnt_action in (BoardState.SETFIRSTTOWN, BoardState.SETSECONDTOWN, BoardState.ACTION) and vertex in self.player_list[self.crnt_player_index].potential_town_pos:
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
    def draw_potential_road(self, edge: tuple[tuple[int,int], tuple[int, int]]):
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
        if edge[0][1] < edge[1][1]:
            self.ways_already_set[edge] = player_index
        else:
            self.ways_already_set[(edge[1], edge[0])] = player_index

    # 開拓地を設置
    def set_town(self, pos: tuple[int,int], player_index: int):
        self.towns_already_set[pos] = player_index

    # 都市を設置
    def set_city(self, pos: tuple[int,int]):
        pass

    def pick_town_pos_from_mouse(self, mouse_pos: tuple[int,int]):
        if self.crnt_action not in (BoardState.ACTION, BoardState.SETFIRSTTOWN, BoardState.SETSECONDTOWN):
            return False
        
        mx, my = mouse_pos
        best_pos = None
        best_dist = None
        for town_pos in self.player_list[self.crnt_player_index].potential_town_pos:
            tx, ty = self.to_screen(town_pos)
            dist = math.hypot(mx - tx, my - ty)
            if dist <= self.VERTEX_RADIUS and (best_dist is None or dist < best_dist):
                best_dist = dist
                best_pos = town_pos

        if best_pos is not None:
            if self.crnt_action == BoardState.ACTION:
                pass
            elif self.crnt_action == BoardState.SETSECONDTOWN:
                self.set_second_town(best_pos)
                resources: list[int] = [0,0,0,0,0]
                for space_index in self.vertex_details[best_pos]:
                    if (resource := self.resources[space_index]) not in ("dessert", "sea"):
                        if resource == "tree":
                            resources[0] += 1
                        elif resource == "brick":
                            resources[1] += 1
                        elif resource == "sheep":
                            resources[2] += 1
                        elif resource == "wheat":
                            resources[3] += 1
                        elif resource == "ore":
                            resources[4] += 1
                        # 金脈の場合
                        else:
                            pass
                self.hand_cards_by_player[self.crnt_player_index].add_resources(resources)
            else:
                self.set_first_town(best_pos)
            return True
        
        return False
    
    def pick_way_pos_from_mouse(self, mouse_pos: tuple[int,int]):
        if self.crnt_action not in (BoardState.ACTION, BoardState.SETFIRSTROAD, BoardState.SETSECONDROAD):
            return False
        
        best_edge = None
        best_dist = None
        for road_edge in self.player_list[self.crnt_player_index].potential_road_pos:
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
            self.player_list[self.crnt_player_index].potential_road_pos.remove(best_edge)
            self.update_potential_ways_from_vertex(best_edge[0], "road")
            self.update_potential_ways_from_vertex(best_edge[1], "road")
            if self.crnt_action == BoardState.SETFIRSTROAD:
                if self.crnt_player_index == 3:
                    self.crnt_action = BoardState.SETSECONDTOWN
                else:
                    self.crnt_action = BoardState.SETFIRSTTOWN
                    self.crnt_player_index += 1 
            elif self.crnt_action == BoardState.SETSECONDROAD:
                if self.crnt_player_index == 0:
                    self.crnt_action = BoardState.ROLLDICE
                else:
                    self.crnt_action = BoardState.SETSECONDTOWN
                    self.crnt_player_index -= 1 
            return True
        
        return False

    def update_potential_town_pos(self):
        self.player_list[self.crnt_player_index].potential_town_pos.difference_update(self.towns_already_set)

    def set_first_town(self, best_pos: tuple[int,int]):
        self.set_town(best_pos, self.player_list[self.crnt_player_index].player_index)
        self.update_potential_town_pos()
        self.update_potential_ways_from_vertex(best_pos, "town")
        self.crnt_action = BoardState.SETFIRSTROAD

    def set_second_town(self, best_pos: tuple[int,int]):
        self.set_town(best_pos, self.player_list[self.crnt_player_index].player_index)
        self.update_potential_town_pos()
        self.update_potential_ways_from_vertex(best_pos, "town")
        self.crnt_action = BoardState.SETSECONDROAD

    def update_potential_ways_from_vertex(self, vertex: tuple[int,int], object_type: str):
        """現在設置した道または開拓地から道を延ばせる辺を新たに取得する"""
        # この頂点からはY字状に辺が伸びている
        if vertex[1] % 3 == 2:
            # まずは左上の頂点との辺を確認
            self.update_potential_edge(vertex, (vertex[0]-2, vertex[1]-1), object_type)
            # 次は下の頂点との辺を確認
            self.update_potential_edge(vertex, (vertex[0], vertex[1]+2), object_type)
            # 最後は右上の頂点との辺を確認
            self.update_potential_edge(vertex, (vertex[0]+2, vertex[1]-1), object_type)

        # この頂点からは上下逆さのY字状に辺が伸びている
        elif vertex[1] % 3 == 1:
            # まずは左下の頂点との辺を確認
            self.update_potential_edge(vertex, (vertex[0]-2, vertex[1]+1), object_type)
            # 次は上の頂点との辺を確認
            self.update_potential_edge(vertex, (vertex[0], vertex[1]-2), object_type)
            # 最後は右下の頂点との辺を確認
            self.update_potential_edge(vertex, (vertex[0]+2, vertex[1]+1), object_type)

    def update_potential_edge(self, start_vertex: tuple[int,int], end_vertex: tuple[int,int], object_type: str):
        # この辺が存在しており、まだそこに道が置かれていないかを見る(後々、海賊で規制されていないかも確認できるようにする)
        edge = tuple(sorted((start_vertex, end_vertex), key=lambda x: x[1]))
        if edge in self.edge_details and edge not in self.ways_already_set:
            # 道が置ける辺であり、先端に自分以外の開拓地がない、前置いたのが船ではない場合は道を置ける
            if self.edge_details[edge]["road"] and self.towns_already_set.get(start_vertex) in (None, self.player_list[self.crnt_player_index].player_index) and object_type != "ship":
                self.player_list[self.crnt_player_index].potential_road_pos.add(edge)
            
            # 船が置ける辺であり、先端に自分以外の開拓地がない、前置いたのが道ではない場合は船を置ける
            if self.edge_details[edge]["ship"] and self.towns_already_set.get(start_vertex) in (None, self.player_list[self.crnt_player_index].player_index) and object_type != "town":
                self.player_list[self.crnt_player_index].potential_ship_pos.add(edge)