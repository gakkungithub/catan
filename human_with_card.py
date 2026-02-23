import math
import numpy as np

class HumanPlayer:
    def __init__(self, player_index: int, possible_town_pos: set[tuple[int, int]]):
        self.possible_town_pos = possible_town_pos
        self.possible_road_pos: set[tuple[tuple[int,int], tuple[int,int]]] = set()
        self.possible_ship_pos: set[tuple[tuple[int,int], tuple[int,int]]] = set()
        self.player_index = player_index
