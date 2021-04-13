# PyTreadmillTask

from pyControl.utility import *
from devices import *
import math
import uarray

# -------------------------------------------------------------------------
# States and events.
# -------------------------------------------------------------------------

states = ['intertrial',
          'trial_start']

initial_state = 'intertrial'
events = [
          'session_timer'
          ]

# -------------------------------------------------------------------------
# Variables.
# -------------------------------------------------------------------------

# general parameters
v.rand_angle = uarray.array('d')

# -------------------------------------------------------------------------
# Define behaviour.
# -------------------------------------------------------------------------

# Run start and stop behaviour.

# State behaviour functions.
def trial_start(event):
    if event == 'entry':
        print('{}, timeBeforeATan'.format(get_current_time()))
        for angle in v.rand_angle:
            a = math.atan2(angle, 1)
        
        print('{}, timeAfterATan'.format(get_current_time()))

        stop_framework()



def intertrial(event):
    if event == 'entry':
        set_timer('session_timer', 10, True)    
        print('{}, timeBeforeRand'.format(get_current_time()))
        for i in range (1000):
            v.rand_angle.append(random()*6.28)

        print('{}, timeAfterRand'.format(get_current_time()))
        goto_state('trial_start')
        
def all_states(event):
    if event == 'session_timer':
        stop_framework()
