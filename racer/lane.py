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

import time
import random
import threading

import pygame

from light import Light
from clock import Clock


class Lane:
    def __init__(self, tree_type="sportsman", delay=0.5, start=None, lane="left",
                 computer=True, perfect=0.0, rollout=0.220, cmin=-0.009,
                 cmax=0.115, surface=None, background=None):
        self.perfect = perfect
        self.rollout = rollout
        self.cmin = cmin
        self.cmax = cmax
        self.surface = surface
        self.rect = self.surface.get_rect()
        self.dirty_rects = []
        self.dirty = False
        self.tree_type = tree_type
        if tree_type == "sportsman":
            self.multiplier = 3
        elif tree_type == "pro":
            self.multiplier = 1
        self.state = None
        self.launched_time = None
        self.start_time = None
        self.foul = threading.Event()
        self.launched = threading.Event()
        self.pre_staged = threading.Event()
        self.staged = threading.Event()
        self.flashing = threading.Event()
        self.y1 = threading.Event()
        self.y2 = threading.Event()
        self.y3 = threading.Event()
        self.g = threading.Event()
        self.reaction = None
        self.dial_in = 0.0
        self.log = []
        self.computer = computer
        self.start = start
        self.delay = delay
        self.state = 0
        self.total_delay = self.delay * self.multiplier
        self.start_time = None
        self.clock_log = []
        clock_rect = pygame.Rect(
            0, self.rect.height - self.rect.height / 7.0,
            self.rect.width, self.rect.height / 7.0)
        clock_rect.bottom = self.rect.height
        self.clock = Clock(clock_rect)
        self.background = pygame.Surface(
            (self.rect.width, self.rect.height),
            flags=pygame.SRCALPHA)
        self.background.blit(
            background,
            (0, 0),
            area=(
                self.surface.get_offset(),
                (self.rect.width, self.rect.height)))
        self.surface.blit(self.background, (0, 0))
        self.lane = lane.lower()
        light_width = (self.rect.height / 7) - (self.rect.height / 35.0)
        self.lights = [
            Light(light_width, light_type='staging'),
            Light(light_width, light_type='staging'),
            Light(light_width, light_type='yellow'),
            Light(light_width, light_type='yellow'),
            Light(light_width, light_type='yellow'),
            Light(light_width, light_type='green'),
            Light(light_width, light_type='red')
        ]
        #if self.lane == "left":
        #    self.offset = int(round(self.rect.width * 0.49, 0))
        #else:
        self.offset = int(round(self.rect.height / 16.5, 0))
        total_offset = self.rect.height / 20.575
        counter = 0
        for light in self.lights:
            if self.lane == "right":
                light.rect.left = self.offset
            else:
                light.rect.right = self.rect.right - self.offset
            light.rect.top = int(round(total_offset, 0))
            if counter == 0:
                total_offset += total_offset / 1.28
            elif counter == 1:
                total_offset -= self.rect.height / 90.0
            else:
                total_offset += (self.rect.height / 700.0) * 1.49
            total_offset += light.rect.height + (self.rect.height * 0.0098)
            counter += 1

    def reset(self):
        self.start_time = None
        self.launched_time = None
        self.foul.clear()
        self.flashing.clear()
        self.launched.clear()
        self.pre_staged.clear()
        self.staged.clear()
        self.y1.clear()
        self.y2.clear()
        self.y3.clear()
        self.g.clear()
        self.clock.reset()
        self.clock_log = []
        for light in self.lights:
            light.off()
        self.pre_stage()

    def pre_stage(self):
        self.pre_staged.set()
        self.state = 0
        self.lights[0].on()
        if self.computer:
            self.stage()

    def stage(self):
        self.state = 1
        self.lights[1].on()
        self.staged.set()

    def _start(self):
        threading.Thread(None, self.timer, name=self.lane + " timer()").start()

    def launch(self):
        self.start.wait()
        if self.computer:
            if self.cmin == self.cmax:
                computer_delay = self.cmin
            else:
                computer_delay = random.randrange(
                    (self.total_delay * 1000) + (self.cmin * 1000),
                    (self.total_delay * 1000 ) + (self.cmax * 1000), 1) / 1000.0
            self.launched_time = self.start_time + computer_delay
            self.launched.set()
        else:
            self.launched.wait()
            self.launched_time += self.rollout
        self.reaction = self.launched_time + self.perfect
        self.reaction -= (self.total_delay + self.start_time) 
        if not self.total_delay + self.start_time - time.time() < 0:
            time.sleep(self.start_time + self.total_delay + self.reaction -self.perfect - time.time())
        if self.reaction < self.perfect:
            self.red()
        self.pre_staged.clear()
        self.lights[0].off()
        self.staged.clear()
        self.lights[1].off()
        self.clock.draw(self.reaction)
        self.log.append(self.reaction)

    def timer(self):
        launch = threading.Thread(None,
            self.launch, name=self.lane + " launch()").start()
        threading.Thread(None,
            self.yellow1, name=self.lane + " yellow1()").start()
        threading.Thread(None,
            self.yellow2, name=self.lane + " yellow2()").start()
        threading.Thread(None,
            self.yellow3, name=self.lane + " yellow3()").start()
        threading.Thread(None,
            self.green, name=self.lane + " green()").start()
        self.state = 2

    def light(self, number=0):
        if self.foul.is_set():
            return False
        if self.tree_type == "pro":
            if number == 3:
                number = 1
            else:
                number = 0
        while time.time() < self.start_time + (self.delay * number):
            if self.foul.is_set():
                return False
        return True

    def yellow1(self):
        self.y1.wait()
        if not self.foul.is_set():
            self.lights[2].on()
            time.sleep(self.delay)
        if not self.foul.is_set():
            self.lights[2].off()

    def yellow2(self):
        if self.tree_type == "pro":
            self.y1.wait()
        else:
            self.y2.wait()
        if not self.foul.is_set():
            self.lights[3].on()
            time.sleep(self.delay)
        if not self.foul.is_set():
            self.lights[3].off()

    def yellow3(self):
        if self.tree_type == "pro":
            self.y1.wait()
        else:
            self.y3.wait()
        if not self.foul.is_set():
            self.lights[4].on()
            time.sleep(self.delay)
        if not self.foul.is_set():
            self.lights[4].off()

    def green(self):
        self.g.wait()
        if not self.foul.is_set():
            self.lights[5].on()

    def red(self):
        self.foul.set()
        self.lights[6].on()
        self.lights[5].off()

    def win(self):
        self.flashing.set()
        threading.Thread(None, self.flash, name=self.lane + " flash()").start()

    def flash(self):
        try:
            while self.flashing.is_set():
                for light in self.lights[2:5]:
                    light.on()
                time.sleep(0.5)
                for light in self.lights[2:5]:
                    light.off()
                time.sleep(0.5)
            for light in self.lights[2:5]:
                light.off()
        except:
            pass

    def draw(self):
        dirty_objects = []
        for light in self.lights + [self.clock]:
            if light.dirty:
                dirty_objects.append(light)
                self.dirty_rects.append(
                    light.rect.move(self.surface.get_offset()))
                light.dirty = False
                if self.dirty:
                    self.dirty = self.dirty.union(light.rect)
                else:
                    self.dirty = light.rect
        if not self.dirty:
            return
        self.surface.blit(
            self.background,
            (self.dirty.left, self.dirty.top),
            area=self.dirty)
        for light in dirty_objects:
            self.surface.blit(light.surface, (light.rect.left, light.rect.top))

