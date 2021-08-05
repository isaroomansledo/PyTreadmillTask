import pyb, machine, time
import pyControl.hardware as _h


class ParallelOdourRelease():
    # mouse motion sensor.
    def __init__(self,
                 Ndirections: int = 5,
                 NstimPerDir: int = 2,
                 *pins: str):

        # PINS should be exactly Ndirections x NstimPerDir strings
        # specifying the pins! iterating over Direction and Odour, Odour ==0 is clean air
        assert len(pins) == Ndirections * NstimPerDir, "wrong number of pins!"

        self.Ndirections = Ndirections
        self.NstimPerDir = NstimPerDir

        counter = 0
        for dir in range(Ndirections):
            for stim in range(NstimPerDir):
                sol = self._sol_name(dir, stim)
                setattr(self, sol, _h.Digital_output(pin=pins[counter]))
                getattr(self, sol).off()

                counter += 1

    def all_off(self):
        for dir in range(self.Ndirections):
            for stim in range(self.NstimPerDir):
                getattr(self, self._sol_name(dir, stim)).off()

    def clean_air_on(self):
        """
        clean air (Odour==0) on everywhere and odourant off.
        """
        for dir in range(self.Ndirections):
            getattr(self, self._sol_name(dir, 0)).on()
            getattr(self, self._sol_name(dir, 1)).off()

    def odour_release(self, dir: int):
        for direction in range(self.Ndirections):
            odour = 1 if direction == dir else 0
            getattr(self, self._sol_name(direction, odour)).on()
            getattr(self, self._sol_name(direction, 1 - odour)).off()

    @staticmethod
    def _sol_name(dir: int, odour: int) -> str:
        return 'Dir' + str(dir) + 'Odour' + str(odour)
