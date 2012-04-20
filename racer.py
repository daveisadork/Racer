#!/bin/env/python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# Code comments? We don't need no stinking code comments!

from __future__ import division

import sys
import time
import random
import thread
import threading

import pygame
from pygame.locals import *


pygame.display.init()
pygame.font.init()

DARK_YELLOW = pygame.Color(63, 47, 0)
DARK_GREEN = pygame.Color(0, 63, 0)
DARK_RED = pygame.Color(63, 0, 0)
YELLOW = pygame.Color(255, 159, 23)
GREEN = pygame.Color(23, 223, 23)
RED = pygame.Color(223, 23, 23)
BLACK = pygame.Color(0, 0, 0)
WHITE = pygame.Color(255, 255, 255)

COLORS = {
    'yellow': {False: DARK_YELLOW, True: YELLOW},
    'red': {False: DARK_RED, True: RED},
    'green': {False: DARK_GREEN, True: GREEN}
}


class Light:
    def __init__(self, width, type='yellow'):
        image = pygame.image.load("lights.png")
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
        self.font = pygame.font.Font("font.ttf", self.text_rect.height)
        self.text_rect = self.surface.get_rect()
        self.dirty = False
    
    def reset(self):
        self.surface.fill(BLACK)
        self.dirty = True
        
    def draw(self, reaction=0.0, color=RED):
        text = self.font.render("%0.3f" % reaction, 1, color)
        text_pos = text.get_rect()
        text_pos.centerx = self.text_rect.centerx
        text_pos.centery = self.text_rect.centery
        self.surface.blit(text, text_pos)
        self.dirty = True


class Lane:
    def __init__(self, type="sportsman", delay=0.5, start=None, lane="left",
                 computer=True, surface=None, background=None):
        self.surface = surface
        self.rect = self.surface.get_rect()
        self.dirty_rects = []
        self.dirty = False
        self.type = type
        if type == "sportsman":
            self.multiplier = 3
        elif type == "pro":
            self.multiplier = 1
        self.state = None
        self.launched_time = None
        self.start_time = None
        self.count = threading.Event()
        self.foul = threading.Event()
        self.launched = threading.Event()
        self.pre_staged = threading.Event()
        self.staged = threading.Event()
        self.flashing = threading.Event()
        self.reaction = None
        self.rollout = 0.220
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
            Light(light_width, type='staging'),
            Light(light_width, type='staging'),
            Light(light_width, type='yellow'),
            Light(light_width, type='yellow'),
            Light(light_width, type='yellow'),
            Light(light_width, type='green'),
            Light(light_width, type='red')
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
        self.count.clear()
        self.foul.clear()
        self.flashing.clear()
        self.launched.clear()
        self.pre_staged.clear()
        self.staged.clear()
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
        self.count.wait()
        if self.computer:
            self.launched.set()
            self.launched_time = self.start_time + (random.randrange(
                (self.total_delay * 1000) - 9,
                (self.multiplier * self.delay * 1000 ) + 115, 1) / 1000)
        else:
            self.launched.wait()
            self.launched_time += self.rollout
        if self.start_time:
            self.reaction = self.launched_time + self.delay
            self.reaction -= (self.total_delay + self.start_time) 
        else:
            #print "Run aborted"
            self.reaction = 0.0
        if not self.total_delay + self.start_time - time.time() < 0:
            time.sleep(self.total_delay + self.start_time - time.time())
        if self.reaction < self.delay:
            self.red()
        self.pre_staged.clear()
        self.lights[0].off()
        self.staged.clear()
        self.lights[1].off()
        self.clock.draw(self.reaction)
        self.log.append(self.reaction)
        if not self.computer:
            print "Round %d: %0.3f" % (len(self.log), self.reaction)

    def timer(self):
        launch = threading.Thread(None,
            self.launch, name=self.lane + " launch()")
        launch.start()
        threading.Thread(None,
            self.yellow1, name=self.lane + " yellow1()").start()
        threading.Thread(None,
            self.yellow2, name=self.lane + " yellow2()").start()
        threading.Thread(None,
            self.yellow3, name=self.lane + " yellow3()").start()
        threading.Thread(None,
            self.green, name=self.lane + " green()").start()
        self.state = 2
        self.start.wait()
        self.count.set()
        launch.join()

    def light(self, number=0):
        if self.foul.is_set():
            return False
        if self.type == "pro":
            if number == 3:
                number = 1
            else:
                number = 0
        while time.time() < self.start_time + (self.delay * number):
            if self.foul.is_set():
                return False
        return True

    def yellow1(self):
        self.count.wait()
        if self.light(0):
            self.lights[2].on()
        time.sleep(self.delay)
        self.lights[2].off()

    def yellow2(self):
        self.count.wait()
        if self.light(1):
            self.lights[3].on()
        time.sleep(self.delay)
        self.lights[3].off()

    def yellow3(self):
        self.count.wait()
        if self.light(2):
            self.lights[4].on()
        time.sleep(self.delay)
        self.lights[4].off()

    def green(self):
        self.count.wait()
        if self.light(3):
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
        

class Tree:
    def __init__(self, type="pro", delay=0.4, left_lane="computer",
                 right_lane="human", debug=False):
        self.two_player = (left_lane == "human" and right_lane == "human")
        self.debug = debug
        self.delay = delay
        self.start = threading.Event()
        self.staged = threading.Event()
        self.quitting = threading.Event()
        self.type = type
        self.tie = []
        self.start_time = None
        self.screen = pygame.display.set_mode(
            (480, 700),
            pygame.HWSURFACE | pygame.DOUBLEBUF )
        self.scale()
        self.left_lane = Lane(
            type=type,
            delay=delay,
            start=self.start,
            lane="left",
            computer=(left_lane=="computer"),
            surface=self.screen.subsurface(
                pygame.Rect(
                    self.rect.left,
                    self.tree_rect.top,
                    self.rect.centerx,
                    self.tree_rect.height)),
            background=self.background)
        self.right_lane = Lane(
            type=type,
            delay=delay,
            start=self.start,
            lane="right",
            computer=(right_lane=="computer"),
            surface=self.screen.subsurface(
                pygame.Rect(
                    self.rect.centerx,
                    self.tree_rect.top,
                    self.rect.centerx,
                    self.tree_rect.height)),
                background=self.background)
        self.lanes = {"left": self.left_lane, "right": self.right_lane}
        if self.two_player:
            self.human = None
        elif right_lane == "human":
            self.human = self.right_lane
        elif left_lane == "human":
            self.human = self.left_lane
        else:
            self.human = self.left_lane
        if self.debug:
            self.font = pygame.font.Font("font.ttf", 50)
            self.fps = self.font.render("", 1, WHITE)
        clock = threading.Thread(None, self.clock, name="clock()")
        monitor = threading.Thread(None, self.thread_monitor,
            name="thread_monitor()")
        clock.start()
        monitor.start()
        self.reset()
        self.event_loop()
        clock.join()
        monitor.join()
     
    def scale(self):
        self.rect = self.screen.get_rect()
        background = pygame.image.load("background.png")
        background.convert()
        background_rect = background.get_rect()
        if self.rect.width / self.rect.height <= 1.6:
            background = pygame.transform.smoothscale(
                background,
                (int(round(self.rect.height * 1.6, 0)), self.rect.height))
        else:
            background = pygame.transform.smoothscale(
                background,
                (self.rect.width, int(round(self.rect.width / 1.6, 0))))
        background_rect = background.get_rect()
        temp_rect = self.rect.move(0, 0)
        temp_rect.centerx = background_rect.centerx
        temp_rect.centery = background_rect.centery
        self.background = background.subsurface(temp_rect)
        self.vignette = pygame.image.load("vignette.png")
        self.vignette.convert_alpha()
        self.vignette = pygame.transform.smoothscale(
            self.vignette,
            (self.rect.width, self.rect.height))
        self.tree = pygame.image.load("tree.png")
        self.tree.convert_alpha()
        self.tree_rect = self.tree.get_rect()
        self.tree_rect = self.tree_rect.fit(self.rect)
        self.tree = pygame.transform.smoothscale(
            self.tree, 
            (self.tree_rect.width, self.tree_rect.height))
        self.tree_rect.midbottom = self.rect.midbottom
        self.background.blit(self.vignette, (0, 0))
        self.background.blit(self.tree, (self.tree_rect.left, 0))
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

    def reset(self):
        self.tie = []
        self.start_time = None
        self.start.clear()
        self.staged.clear()
        for lane in self.lanes.values():
            lane.reset()
        threading.Thread(None, self.staging, name="staging()").start()

    def staging(self):
        while (not self.quitting.is_set() and
          not (self.left_lane.staged.is_set() and
          self.right_lane.staged.is_set())):
            time.sleep(0.001)
        if self.quitting.is_set():
            return
        self.start_time = time.time() + random.randrange(1000,3000,1) / 1000
        if self.left_lane.staged.is_set() and self.right_lane.staged.is_set():
            self.staged.set()
        else:
            self.reset()
            return
        while (time.time() < self.start_time and
          self.left_lane.staged.is_set() and
          self.right_lane.staged.is_set()):
            time.sleep(0.001)
        if self.left_lane.staged.is_set() and self.right_lane.staged.is_set():
            threading.Thread(None, self.race, name="race()").start()
        else:
            self.reset()
            return
    
    def race(self):
        self.left_lane.start_time = self.right_lane.start_time = self.start_time
        left = threading.Thread(None, self.left_lane.timer,
            name="Left Lane timer()")
        right = threading.Thread(None, self.right_lane.timer,
            name="Right Lane timer()")
        left.start()
        right.start()
        self.start.set()
        self.left_lane.launched.wait()
        self.right_lane.launched.wait()
        left.join()
        right.join()
        #print "Left start time: %0.7f" % self.left_lane.start_time
        #print "Right start time: %0.7f" % self.right_lane.start_time
        if self.two_player:
            if self.tie[0].foul.is_set():
                self.tie[1].win()
            else:
                self.tie[0].win()
        elif self.left_lane.reaction < self.right_lane.reaction:
            if self.left_lane.foul.is_set():
                if self.right_lane.foul.is_set():
                    self.right_lane.win()
                    #print "Winner: Right Lane RT %0.3f (foul)" % self.right_lane.reaction
                    #print "Loser:  Left Lane  RT %0.3f (foul)" % self.left_lane.reaction
                self.right_lane.win()
                #print "Winner: Right Lane RT %0.3f" % self.right_lane.reaction
                #print "Loser:  Left Lane  RT %0.3f (foul)" % self.left_lane.reaction
            else:
                self.left_lane.win()
                #print "Winner: Left Lane  RT %0.3f" % self.left_lane.reaction
                #print "Loser:  Right Lane RT %0.3f" % self.right_lane.reaction
        elif self.right_lane.reaction < self.left_lane.reaction:
            if self.right_lane.foul.is_set():
                if self.left_lane.foul.is_set():
                    self.left_lane.win()
                    #print "Winner: Left Lane  RT %0.3f (foul)" % self.left_lane.reaction
                    #print "Loser:  Right Lane RT %0.3f (foul)" % self.right_lane.reaction
                self.left_lane.win()
                #print "Winner: Left Lane  RT %0.3f" % self.left_lane.reaction
                #print "Loser:  Right Lane RT %0.3f (foul)" % self.right_lane.reaction
            else:
                self.right_lane.win()
                #print "Winner: Right Lane RT %0.3f" % self.right_lane.reaction
                #print "Loser:  Left Lane  RT %0.3f" % self.left_lane.reaction
        elif self.left_lane.reaction == self.right_lane.reaction:
            for lane in self.lanes.values():
                if lane.computer is True:
                    lane.lose()
                elif lane.computer is False:
                    lane.win()
     
    def win(self, lane):
        self.lanes[lane].win()
    
    def event_loop(self):
        pygame.event.set_allowed(None)
        pygame.event.set_allowed([KEYDOWN, KEYUP, QUIT])
        while not self.quitting.is_set(): 
            event = pygame.event.wait()
            if event.type == KEYDOWN and event.key in [K_m, K_z, K_SPACE]:
                if self.two_player:
                    if not (self.right_lane.pre_staged.is_set() or
                      self.left_lane.pre_staged.is_set()):
                        self.reset()
                    elif (event.key == K_m and
                      self.right_lane.pre_staged.is_set()):
                        self.right_lane.stage()
                    elif (event.key == K_z and
                      self.left_lane.pre_staged.is_set()):
                        self.left_lane.stage()
                elif event.key == K_SPACE:
                    if self.human.pre_staged.is_set():
                        self.human.stage()
                        #while pygame.key.get_pressed()[K_SPACE]:
                        #    pygame.event.pump()
                        #if self.human.staged.is_set() and self.start.is_set():
                        #    self.human.launched_time = time.time()
                        #    self.human.launched.set()
                        #else:
                        #    self.human.staged.clear()
                        #    self.human.lights[1].off()
                    else:
                        self.reset()
            elif event.type == KEYUP and event.key in [K_m, K_z, K_SPACE]:
                if self.two_player:
                    if event.key == K_m:
                        if (self.right_lane.staged.is_set()
                          and self.start.is_set()):
                            self.right_lane.launched_time = time.time()
                            self.right_lane.launched.set()
                            self.tie.append(self.right_lane)
                        else:
                            self.right_lane.staged.clear()
                            self.right_lane.lights[1].off()
                    elif event.key == K_z:
                        if (self.left_lane.staged.is_set() and
                          self.start.is_set()):
                            self.left_lane.launched_time = time.time()
                            self.left_lane.launched.set()
                            self.tie.append(self.left_lane)
                        else:
                            self.left_lane.staged.clear()
                            self.left_lane.lights[1].off()                                
                elif event.key == K_SPACE:
                    if self.human.staged.is_set() and self.start.is_set():
                        self.human.launched_time = time.time()
                        self.human.launched.set()
                    else:
                        self.human.staged.clear()
                        self.human.lights[1].off()
            elif (event.type == pygame.QUIT or
              (event.type == KEYDOWN and event.key in [K_ESCAPE, K_q])):
                self.quit()
            #print event
    
    def draw(self):
        if self.debug:
            fps_rect = self.fps.get_rect()
            fps_rect.top = 10
            fps_rect.left = 10
        self.left_lane.draw()
        self.right_lane.draw()
        dirty = []
        if self.left_lane.dirty:
            dirty += self.left_lane.dirty_rects
            self.left_lane.dirty = False
            self.left_lane.dirty_rects = []
        if self.right_lane.dirty:
            dirty += self.right_lane.dirty_rects
            self.right_lane.dirty = False
            self.right_lane.dirty_rects = []
        if self.debug:
            self.screen.blit(self.fps, (fps_rect.left, fps_rect.top))
        if dirty:
            pygame.display.update(dirty)

    def clock(self):
        clock = pygame.time.Clock()
        while not self.quitting.is_set():
            if self.debug:
                self.fps = self.font.render("%0.1f" % clock.get_fps(), 1, WHITE)
            clock.tick()
            self.draw()
  
    def thread_monitor(self):
        if not self.debug:
            return
        last_count = 0
        while not self.quitting.is_set():
            if threading.active_count() == last_count:
                continue
            else:
                last_count = threading.active_count()
            print "\nActive threads:"
            for thread in sorted(threading.enumerate(),
              key=threading.Thread.getName):
                print "  " + thread.name
            
    def quit(self):
        self.left_lane.flashing.clear()
        self.right_lane.flashing.clear()
        self.quitting.set()
        if self.human.log:
            best = None
            worst = None
            for react in self.human.log:
                if not best and not worst:
                    worst = best = react
                if react < best and react >= self.delay:
                    best = react
                if react > best and best < self.delay:
                    best = react
                if react > worst:
                    worst = react
            print "Best: %0.3f" % best
            print "Worst: %0.3f" % worst
            print "Average: %0.3f" % round(sum(
                self.human.log)/len(self.human.log), 3)
        pygame.quit()


if __name__ == "__main__":
    tree = Tree()
