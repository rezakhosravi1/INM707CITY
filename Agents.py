import numpy as np
from collections import namedtuple
from enum import Enum
import sys
import os
import time
import copy
from IPython.display import clear_output
import pandas as pd 

class Agents(bytes, Enum):

    def __new__(cls, value, frame, health, speed, reward):
        obj = bytes.__new__(cls, [value])
        obj._value_ = value
        obj.frame = frame
        obj.health = health
        obj.speed = speed
        obj.reward = reward
        return obj
    PLAYER = (0, " ___\n/o o\\\n\\_-_/", 10, 5, -10)
    ENEMY_WEAK = (1, " __ \n/--\\\n|oo|", 2, 1, 5)
    ENEMY_STRONG = (2, " __ \n/~~\\\n|**|", 4, 1, 10)
    ENEMY_UFO = (3, " _/_\\_\n<_ O _>\n  \\ /  ", 5, 3, 20)
    BULLET = (4, "-", 1, 10, 0)
    BOMB = (5, "O", 2, 7, 0)
