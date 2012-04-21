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
from pygame.locals import *

from lane import Lane


class Tree:
    def __init__(self, tree_type="pro", delay=0.4, left_lane="computer",
                 right_lane="human", debug=False, perfect=0.0,
                 left_rollout=0.220, right_rollout=0.220, stats=False,
                 amin=1.0, amax=3.0, cmin=-0.009, cmax=0.115, auto_reset=False,
                 res="480x700", fullscreen=False, hw=False, doublebuf=False):
        self.perfect = perfect
        self.left_rollout = left_rollout
        self.right_rollout = right_rollout
        self.amin = amin
        self.amax = amax
        self.auto_reset = auto_reset
        self.two_player = (left_lane == "human" and right_lane == "human")
        self.debug = debug
        self.stats = stats
        self.delay = delay
        self.start = threading.Event()
        self.staged = threading.Event()
        self.quitting = threading.Event()
        self.tree_type = tree_type
        self.tie = []
        self.start_time = None
        self.clock = pygame.time.Clock()
        flags = 0
        if hw:
            flags = flags | pygame.HWSURFACE
        if doublebuf:
            flags = flags | pygame.DOUBLEBUF
        if fullscreen:
            resolution = (0, 0)
            flags = flags | pygame.FULLSCREEN
            pygame.mouse.set_visible(False)
        else:
            width, height = res.split("x")
            resolution = (int(width), int(height))
        self.screen = pygame.display.set_mode(resolution, flags)
        self.scale()
        self.left_lane = Lane(
            tree_type=tree_type,
            delay=delay,
            start=self.start,
            lane="left",
            computer=(left_lane=="computer"),
            perfect=perfect,
            rollout=left_rollout,
            cmin=cmin,
            cmax=cmax,
            surface=self.screen.subsurface(
                pygame.Rect(
                    self.rect.left,
                    self.tree_rect.top,
                    self.rect.centerx,
                    self.tree_rect.height)),
            background=self.background)
        self.right_lane = Lane(
            tree_type=tree_type,
            delay=delay,
            start=self.start,
            lane="right",
            computer=(right_lane=="computer"),
            perfect=perfect,
            rollout=right_rollout,
            cmin=cmin,
            cmax=cmax,
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
            self.font = pygame.font.Font("assets/font.ttf", 50)
            self.fps = self.font.render("", 1, (255, 255, 255))
        clock = threading.Thread(None, self._clock, name="clock()")
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
        background = pygame.image.load("assets/background.png")
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
        self.vignette = pygame.image.load("assets/vignette.png")
        self.vignette.convert_alpha()
        self.vignette = pygame.transform.smoothscale(
            self.vignette,
            (self.rect.width, self.rect.height))
        self.tree = pygame.image.load("assets/tree.png")
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
        if self.quitting.is_set():
            return
        threading.Thread(None, self.staging, name="staging()").start()

    def staging(self):
        while (not self.quitting.is_set() and
          not (self.left_lane.staged.is_set() and
          self.right_lane.staged.is_set())):
            time.sleep(0.001)
        if self.quitting.is_set():
            return
        # The following line sets the window for the randomized delay between
        # both lanes having fully staged and the race starting.
        if self.amin == self.amax:
            autostart = self.amin
        else:
            autostart = random.randrange(
                self.amin * 1000.0, self.amax * 1000.0, 1) / 1000.0
        self.start_time = time.time() + autostart
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
        if self.human.log and self.stats:
            print "Round %d: %0.3f" % (len(self.human.log), self.human.reaction)
        if self.auto_reset:
            time.sleep(self.auto_reset)
            self.reset()
     
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
            self.fps = self.font.render("%0.1f" % self.clock.get_fps(),
                    1, (255, 255, 255))
            fps_rect = self.fps.get_rect()
            fps_rect.top = 10
            fps_rect.left = 10
            self.screen.blit(self.background, (fps_rect.left, fps_rect.top), fps_rect)
            self.screen.blit(self.fps, (fps_rect.left, fps_rect.top))
            dirty.append(fps_rect)
        if dirty:
            pygame.display.update(dirty)

    def _clock(self):
        while not self.quitting.is_set():             
            self.clock.tick()
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
        self.quitting.set()
        self.reset()
        if self.human.log and self.stats:
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
