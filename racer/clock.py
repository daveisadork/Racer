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


class Clock:
    def __init__(self, rect):
        pos = rect.inflate(
            -int(0.2 * rect.width),
            -int(0.2 * rect.height))
        self.rect = pygame.Rect(0, 0, 212, 100).fit(pos)
        
        text_rect = pygame.Rect(0, 0, 212, 100)
        self.text_rect = text_rect.fit(
                self.rect.inflate(
                -int(text_rect.width * 0.1),
                -int(text_rect.height * 0.1)))
        self.surface = pygame.Surface((self.rect.width, self.rect.height))
        self.font = pygame.font.Font("assets/font.ttf", self.text_rect.height)
        self.text_rect = self.surface.get_rect()
        self.dirty = False
    
    def reset(self):
        self.surface.fill((0, 0, 0))
        self.dirty = True
        
    def draw(self, reaction=0.0, color=(223, 23, 23)):
        text = self.font.render("%0.3f" % reaction, 1, color)
        text_pos = text.get_rect()
        text_pos.centerx = self.text_rect.centerx
        text_pos.centery = self.text_rect.centery
        self.surface.blit(text, text_pos)
        self.dirty = True

