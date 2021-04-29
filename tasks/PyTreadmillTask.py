# PyTreadmillTask

from pyControl.utility import *
import hardware_definition as hw
from devices import *
import math
import uarray, utime

# -------------------------------------------------------------------------
# States and events.
# -------------------------------------------------------------------------

states = ['intertrial']

events = ['session_timer','burst']

initial_state = 'intertrial'

# -------------------------------------------------------------------------
# Variables.
# -------------------------------------------------------------------------
v.flag = False

# session params
v.session_duration = 300 * second  # 1 * hour
# -------------------------------------------------------------------------
# Define behaviour.
# -------------------------------------------------------------------------


# Run start and stop behaviour.
def run_start():
    # Code here is executed when the framework starts running.
    set_timer('session_timer', v.session_duration, True)

    hw.motionSensor.power_up()
    #hw.motionSensor.select.on()
    
    set_timer('burst', 1*ms) 


def run_end():
    # Code here is executed when the framework stops running.
    # Turn off all hardware outputs.
    hw.motionSensor.shut_down()
    hw.off()


# State behaviour functions.
def intertrial(event):
    if event == 'motion':
        print('MO')
        #hw.motionSensor.select.on()
    elif event == 'burst':
        set_timer('burst', 1*ms) 
    


# State independent behaviour.
def all_states(event):
    # Code here will be executed when any event occurs,
    # irrespective of the state the machine is in.
    if event == 'motion': pass
    elif event == 'burst':
        a,b = hw.motionSensor.read_pos()
        if a != b:
            print((a,b))

    elif event == 'session_timer':
        stop_framework()
