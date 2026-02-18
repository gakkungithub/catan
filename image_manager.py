import os
import pygame

class ImageManager:
    _cache: dict[str, pygame.Surface] = {}

    @classmethod
    def load(cls, name: str) -> pygame.Surface:
        if name not in cls._cache:
            path = os.path.join("images", f"{name}.png")
            cls._cache[name] = pygame.image.load(path).convert_alpha()
        return cls._cache[name]