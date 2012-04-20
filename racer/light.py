#!/bin/env/python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# Code comments? We don't need no stinking code comments!


import pygame


class Light:
    def __init__(self, width, type='yellow'):
        image = pygame.image.load("assets/lights.png")
        image = image.convert_alpha()
        types_on = {
            'staging': (200, 0, 200, 100),
            'yellow': (200, 100, 200, 200),
            'green': (200, 300, 200, 200),
            'red': (200, 500, 200, 200)
        }
        types_off = {
            'staging': (0, 0, 200, 100),
            'yellow': (0, 100, 200, 200),
            'green': (0, 300, 200, 200),
            'red': (0, 500, 200, 200)
        }
        if type == "staging":
            self.surface = pygame.Surface((width, width / 2.0))
        else:
            self.surface = pygame.Surface((width, width))
        on = image.subsurface(types_on[type])
        off = image.subsurface(types_off[type])
        self.images = [
            pygame.transform.smoothscale(
                off,
                (int(round(self.surface.get_width(), 0)),
                 int(round(self.surface.get_height(), 0)))),
            pygame.transform.smoothscale(
                on,
                (int(round(self.surface.get_width(), 0)),
                 int(round(self.surface.get_height(), 0))))
        ]
        self.status = False
        self.rect = self.surface.get_rect()
        self.draw()
    
    def draw(self, active=False):
        self.surface = self.images[int(active)]
        self.dirty = True

    def on(self):
        self.draw(True)
        self.status = True
    
    def off(self):
        self.draw(False)
        self.status = False
