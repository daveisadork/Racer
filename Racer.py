#!/bin/env python

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

import os
import sys
from ConfigParser import ConfigParser
from optparse import OptionParser

import racer
from racer.tree import Tree


def get_config():
    config = ConfigParser()
    config.add_section("tree")
    config.set("tree", "type", "pro400")
    config.set("tree", "auto_reset", "0")
    config.set("tree", "zero_perfect", False)
    config.set("tree", "autostart_min", 1.0)
    config.set("tree", "autostart_max", 3.0)
    config.add_section("player")
    config.set("player", "left_lane", "computer")
    config.set("player", "right_lane", "human")
    config.set("player", "left_rollout", 0.220)
    config.set("player", "right_rollout", 0.220)
    config.add_section("display")
    config.set("display", "fullscreen", False)
    config.set("display", "resolution", "480x700")
    config.set("display", "hardware_accel", False)
    config.set("display", "double_buffering", False)
    config.add_section("computer")
    config.set("computer", "reaction_min", -0.009)
    config.set("computer", "reaction_max", 0.115)
    if os.path.exists("config.cfg"):
        config.read("config.cfg")
    else:
        with open("config.cfg", "wb") as config_file:
            config.write(config_file)
    return config


def get_options():
    config = get_config()
    parser = OptionParser()
    parser.add_option("-t", "--tree",
        action="store", dest="tree_type", metavar="TYPE", default=config.get("tree", "type"), 
        help="Sets tree type <pro400|pro500|sportsman>        [default: %default]")
    parser.add_option("-r", "--auto-reset",
        action="store", type="float", dest="auto_reset", metavar="SECS", default=config.getfloat("tree", "auto_reset"),
        help="Sets auto reset time in seconds (0 to disable). [default: %default]")
    parser.add_option("-0", "--zero-perfect",
        action="store_true", dest="perfect", default=config.getboolean("tree", "zero_perfect"),
        help="Shows a perfect reaction time as 0.000")
    parser.add_option("-f", "--fullscreen",
        action="store_true", dest="fullscreen", default=config.getboolean("display", "fullscreen"),
        help="Enables fullscreen mode.")
    parser.add_option("-w", "--window-size",
        action="store", type="string", dest="window", metavar="WxH", default=config.get("display", "resolution"), 
        help="Sets the windowed resolution (ignored if fullscreen) [default: %default]")
    parser.add_option("--left-lane",
        action="store", type="string", dest="left_lane", metavar="PLAYER", default=config.get("player", "left_lane"), 
        help="Sets left lane player type <computer|human>     [default: %default]")
    parser.add_option("--right-lane",
        action="store", type="string", dest="right_lane", metavar="PLAYER", default=config.get("player", "right_lane"), 
        help="Sets right lane player type <computer|human>    [default: %default]")
    parser.add_option("--left-rollout",
        action="store", type="float", dest="left_rollout", metavar="SECS", default=config.getfloat("player", "left_rollout"),
        help="Sets left lane rollout time in seconds.         [default: %default]")
    parser.add_option("--right-rollout",
        action="store", type="float", dest="right_rollout", metavar="SECS", default=config.getfloat("player", "right_rollout"),
        help="Sets right lane rollout time in seconds.        [default: %default]")
    parser.add_option("--autostart-min",
        action="store", type="float", dest="amin", metavar="SECS", default=config.getfloat("tree", "autostart_min"),
        help="Sets the minimum delay for autostart in seconds. [default: %default]")
    parser.add_option("--autostart-max",
        action="store", type="float", dest="amax", metavar="SECS", default=config.getfloat("tree", "autostart_max"),
        help="Sets the maximum delay for autostart in seconds. [default: %default]")
    parser.add_option("--computer-reaction-min",
        action="store", type="float", dest="cmin", metavar="SECS", default=config.getfloat("computer", "reaction_min"),
        help="Sets minimum computer reaction time in seconds. [default: %default]")
    parser.add_option("--computer-reaction-max",
        action="store", type="float", dest="cmax",  metavar="SECS", default=config.getfloat("computer", "reaction_max"),
        help="Sets maximum computer reaction time in seconds. [default: %default]")
    parser.add_option("-b", "--double-buffering",
        action="store_true", dest="doublebuf", default=config.getboolean("display", "double_buffering"),
        help="Enables double buffering.")
    parser.add_option("-a", "--hardware-accel",
        action="store_true", dest="hw", default=config.getboolean("display", "hardware_accel"),
        help="Enables hardware acceleration (fullscreen only).")
    parser.add_option("-s", "--stats",
        action="store_true", dest="stats", default=False,
        help="Shows statistics for the current session.")
    parser.add_option("-d", "--debug",
        action="store_true", dest="debug", default=False,
        help="Shows debugging output.")
    options, args = parser.parse_args()
    options.tree_type = options.tree_type.lower()
    options.left_lane = options.left_lane.lower()
    options.right_lane = options.right_lane.lower()
    if options.tree_type not in ['pro400', 'pro500', 'sportsman']:
        print "Tree type must be pro400, pro500 or sportsman.\n\n"
        parser.print_help()
        sys.exit()
    if (options.left_lane not in ['computer', 'human']
      or options.right_lane not in ['computer', 'human']):
        print "Player type must be computer or human.\n\n"
        parser.print_help()
        sys.exit()
    if options.amin > options.amax:
        print "Autostart minimum must be less than autostart maximum.\n\n"
        parser.print_help()
        sys.exit()
    if options.cmin > options.cmax:
        print "Minimum computer reaction must be less than maximum reaction.\n\n"
        parser.print_help()
        sys.exit()
    if options.amin < 0.0:
        print "Autostart minimum cannot be a negative number.\n\n"
        parser.print_help()
        sys.exit()
    return (options, args)


if __name__ == "__main__":
    (options, args) = get_options()
    if options.tree_type == "sportsman":
        tree_type = "sportsman"
        delay = 0.5
    else:
        tree_type = "pro"
        delay = float(options.tree_type[3:]) / 1000.0
    if options.perfect:
        perfect = 0.0
    else:
        perfect = delay
    tree = Tree(tree_type=tree_type, delay=delay, left_lane=options.left_lane,
                right_lane=options.right_lane, left_rollout=options.left_rollout,
                right_rollout=options.right_rollout, debug=options.debug,
                perfect=perfect, amax=options.amax, amin=options.amin,
                cmax=options.cmax, cmin=options.cmin,
                stats=options.stats, auto_reset=options.auto_reset,
                res=options.window, fullscreen=options.fullscreen,
                hw=options.hw, doublebuf=options.doublebuf)

