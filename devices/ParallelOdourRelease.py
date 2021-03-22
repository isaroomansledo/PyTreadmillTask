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
        assert len(pins) == Ndirections * NstimPerDir, "wrong number of pins!"

        self.Ndirections = Ndirections
        self.NstimPerDir = NstimPerDir

        counter = 0
        for dir in range(Ndirections):
            for stim in range(NstimPerDir):
                tmp = _h.Digital_output(pin=pins[counter])
                self.__dict__[self._sol_name(dir, stim)] = tmp
                tmp.off()

                counter += 1

    def all_off(self):
        for dir in range(self.Ndirections):
            for stim in range(self.NstimPerDir):
                self.__dict__[self._sol_name(dir, stim)].off()

    def clean_air_on(self):
        """
        Odour ==0 for clean air, for any direction
        """
        for dir in range(self.Ndirections):
            self.__dict__[self._sol_name(dir, 0)].on()

    def odour_release(self, dir: int):
        for direction in range(self.Ndirections):
            odour = 1 if direction == dir else 0

            self.__dict__[self._sol_name(direction, odour)].on()

    @staticmethod
    def _sol_name(dir: int, odour: int) -> str:
        return 'Dir' + str(dir) + 'Odour' + str(odour)
