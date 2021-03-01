# PyTreadmillTask

from pyControl.utility import *
import hardware_definition as hw
from devices import *

# -------------------------------------------------------------------------
# States and events.
# -------------------------------------------------------------------------

states = ['intertrial',
          'trial_start',
          'odour_release',
          'reward',
          'penalty']

events = ['motion',
          'lick',
          'session_timer',
          ]

initial_state = 'intertrial'

# -------------------------------------------------------------------------
# Variables.
# -------------------------------------------------------------------------

v.delta_x = []
v.delta_y = []

v.session_duration = 5* second  # 1 * hour
v.reward_duration = 100 * ms  
v.trial_number = 0
v.min_IT_movement = 10  # cm

# -------------------------------------------------------------------------
# Define behaviour.
# -------------------------------------------------------------------------


# Run start and stop behaviour.
def run_start():
    # Code here is executed when the framework starts running.
    set_timer('session_timer', v.session_duration)


def run_end():
    # Code here is executed when the framework stops running.
    # Turn off all hardware outputs.
    hw.off()


# State behaviour functions.
def intertrial(event):
    if event == 'left_poke':
        if withprob(1/v.ratio):
            goto_state('reward_available')


def trial_start(event):
    # 'right_poke' event causes transition to 'reward' state.
    if event == 'right_poke':
        goto_state('reward')


def odour_release(event):
    # On entry turn on solenoid and set timer, when timer elapses goto_state
    # 'wait_for_poke' state, on exit turn of solenoid. 
    if event == 'entry':
        timed_goto_state('reward', v.reward_duration)
        hw.odourDelivery.Dir2Odour1.on()
        v.rewards_obtained += 1
        print('Rewards obtained: {}'.format(v.rewards_obtained))
    elif event == 'exit':
        pass


def reward(event):
    # 'right_poke' event causes transition to 'reward' state.
    if event == 'right_poke':
        goto_state('reward')


def penalty(event):
    # 'right_poke' event causes transition to 'reward' state.
    if event == 'right_poke':
        goto_state('reward')


# State independent behaviour.
def all_states(event):
    # Code here will be executed when any event occurs,
    # irrespective of the state the machine is in.
    # When 'session_timer' event occurs stop framework to end session.
    if event == 'motion':
        # read the motion registers and and append the variables
        delta_x, delta_y = hw.motionSensor.read_pos()
        v.delta_x.append(delta_x)
        v.delta_y.append(delta_y)

        print('{},{}'.format(v.delta_x[-1], v.delta_y[-1]))

    elif event == 'session_timer':
        stop_framework()
