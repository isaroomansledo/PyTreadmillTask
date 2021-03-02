from pyControl.utility import *
import hardware_definition as hw
from devices import *


def single_odourant_random(event):
    if event == 'entry':
        v.delta_x, v.delta_y = [], []
