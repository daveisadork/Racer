#!/bin/env/python

# Racer - A drag racing practice tree
# Copyright 2012 Dave Hayes <dwhayes@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# Code comments? We don't need no stinking code comments!


import pygame


ON = {
    'staging': (200, 0, 200, 100),
    'yellow': (200, 100, 200, 200),
    'green': (200, 300, 200, 200),
    'red': (200, 500, 200, 200)}
OFF = {
    'staging': (0, 0, 200, 100),
    'yellow': (0, 100, 200, 200),
    'green': (0, 300, 200, 200),
    'red': (0, 500, 200, 200)}


class Light:
    def __init__(self, width, light_type='yellow'):
        image = pygame.image.load("assets/lights.png")
        image = image.convert_alpha()
        if light_type == "staging":
            self.surface = pygame.Surface((width, width / 2.0))
        else:
            self.surface = pygame.Surface((width, width))
        on = image.subsurface(ON[light_type])
        off = image.subsurface(OFF[light_type])
        self.images = [
            pygame.transform.smoothscale(
                off,
                (int(round(self.surface.get_width(), 0)),
                 int(round(self.surface.get_height(), 0)))),
            pygame.transform.smoothscale(
                on,
                (int(round(self.surface.get_width(), 0)),
                 int(round(self.surface.get_height(), 0))))]
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
