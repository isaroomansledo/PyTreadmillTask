from pyControl.utility import *
from devices import *
import utime, math


def single_odourant_random(odourDevice: ParallelOdourRelease, delay: float = 0):
    """
    Releases 1 odourant at a random direction
    delay: turn everything off for a 'delay' period, in seconds
    """
    stimDir = randint(0, odourDevice.Ndirections - 1)
    odourDevice.all_off()
    utime.sleep(delay)
    odourDevice.odour_release(stimDir)

    print('{}, odourant_direction'.format(stimDir))

    return stimDir


_pi = math.pi
_target_angle = {0: 5 * _pi / 6,
                 1: 2 * _pi / 3,
                 2: _pi / 2,
                 3: _pi / 3,
                 4: _pi / 6}


def arrived_to_target(dX: float, dY: float,
                      odourant_direction: int,
                      distance_to_target: float,
                      target_angle_tolerance: float):
    """
    checks the motion critereon
    MUST have 5 odour directions
    """
    assert odourant_direction < 5, 'wrong direction value'

    movement = math.sqrt(dX**2 + dY**2)
    if movement < distance_to_target:
        return None

    else:
        move_angle = math.atan2(dY, dX)
        if abs(move_angle - _target_angle[odourant_direction]) < target_angle_tolerance:
            return True
        else:
            return False
