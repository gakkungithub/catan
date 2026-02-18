import math
import numpy as np

class HumanPlayer:
    def __init__(self, player_index: int, potential_town_pos: set[tuple[int, int]]):
        self.potential_town_pos = potential_town_pos
        self.potential_road_pos: set[tuple[tuple[int,int], tuple[int,int]]] = set()
        self.potential_ship_pos: set[tuple[tuple[int,int], tuple[int,int]]] = set()
        self.player_index = player_index
