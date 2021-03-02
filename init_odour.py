from pyControl.utility import *
from devices import *
import utime


def single_odourant_random(odourDevice: ParallelOdourRelease, delay: float = 0):
    """
    Releases 1 odourant at a random direction
    delay: turn everything off for a 'delay' period, in seconds
    """
    stimDir = randint(0, odourDevice.Ndirections - 1)
    odourDevice.all_off()
    utime.sleep(delay)
    odourDevice.odour_release(stimDir)
