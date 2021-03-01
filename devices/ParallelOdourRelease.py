import pyb, machine, time
import pyControl.hardware as _h


class ParallelOdourRelease():
    # mouse motion sensor.
    def __init__(self,
                 Ndirections: int = 5,
                 NstimPerDir: int = 2,
                 *pins: str):

        # PINS should be exactly Ndirections x NstimPerDir strings
        # specifying the pins! iterating over Direction and Odour
        assert len(pins) == Ndirections*NstimPerDir, "wrong number of pins!"

        counter = 0
        for dir in range(Ndirections):
            for stim in range(NstimPerDir):
                self.__dict__['Dir' + str(dir+1) + 'Odour' + str(stim+1)] = _h.Digital_output(pin=pins[counter])
                counter += 1
