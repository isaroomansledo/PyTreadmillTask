import utime, machine, pyb
from pyControl.hardware import *
from devices.PMW3360DM_srom_0x04 import PROGMEM


def twos_comp(val, bits=16):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)         # compute negative value
    return val                          # return positive value as is


class PMW3360DM():
    # mouse motion sensor.
    def __init__(self,
                 SPI_type: str,
                 eventName: str = None,
                 reset: str = None,
                 MT: str = None,
                 CS: str = None,
                 MI: str = None,
                 MO: str = None,
                 SCK: str = None):

        self.MT = MT
        # SPI_type = 'SPI1' or 'SPI2' or 'softSPI'
        SPIparams = {'baudrate': 1000_000, 'polarity': 1, 'phase': 1,
                     'bits': 8, 'firstbit': machine.SPI.MSB}
        if '1' in SPI_type:
            self.SPI = machine.SPI(1, **SPIparams)
            self.select = Digital_output(pin='W7', inverted=True)

        elif '2' in SPI_type:
            self.SPI = machine.SPI(2, **SPIparams)
            self.select = Digital_output(pin='W45', inverted=True)

        elif 'soft' in SPI_type.lower():
            self.SPI = machine.SoftSPI(baudrate=500000, polarity=1, phase=0, bits=8, firstbit=machine.SPI.MSB,
                                       sck=machine.Pin(id=SCK, mode=machine.Pin.OUT, pull=machine.Pin.PULL_DOWN),
                                       mosi=machine.Pin(id=MO, mode=machine.Pin.OUT, pull=machine.Pin.PULL_DOWN),
                                       miso=machine.Pin(id=MI, mode=machine.Pin.IN))
            self.select = Digital_output(pin=CS, inverted=True)

        if MT is not None:
            self.motion = Digital_input(pin=self.MT, falling_event=eventName, pull='up')
        if reset is not None:
            self.reset = Digital_output(pin=reset, inverted=True)
            self.reset.off()

        self.select.off()

    def read_pos(self):
        # write and read Motion register to lock the content of delta registers
        self.write_register(0x02, 0x01)
        self.read_register(0x02)

        delta_x_L = self.read_register(0x03)
        delta_x_H = self.read_register(0x04)
        delta_y_L = self.read_register(0x05)
        delta_y_H = self.read_register(0x06)

        delta_x = delta_x_H + delta_x_L
        delta_y = delta_y_H + delta_y_L

        delta_x = int.from_bytes(delta_x, 'big')
        delta_y = int.from_bytes(delta_y, 'big')

        delta_x = twos_comp(delta_x)
        delta_y = twos_comp(delta_y)

        return delta_x, delta_y

    def read_register(self, addrs: int):
        """
        addrs < 128
        """
        # ensure MSB=0
        addrs = addrs & 0x7f
        addrs = addrs.to_bytes(1, 'little')
        self.select.on()
        self.SPI.write(addrs)
        utime.sleep_us(100)  # tSRAD
        data = self.SPI.read(1)
        utime.sleep_us(1)  # tSCLK-NCS for read operation is 120ns
        self.select.off()
        utime.sleep_us(19)  # tSRW/tSRR (=20us) minus tSCLK-NCS
        return data

    def write_register(self, addrs: int, data: int):
        """
        addrs < 128
        """
        # flip the MSB to 1:
        addrs = addrs | 0x80
        addrs = addrs.to_bytes(1, 'little')
        data = data.to_bytes(1, 'little')
        self.select.on()
        self.SPI.write(addrs)
        self.SPI.write(data)
        utime.sleep_us(20)  # tSCLK-NCS for write operation
        self.select.off()
        utime.sleep_us(100)  # tSWW/tSWR (=120us) minus tSCLK-NCS. Could be shortened, but is looks like a safe lower bound

    def power_up(self):
        """
        Perform the power up sequence
        As per page 26 of datasheet
        """
        # 2
        self.select.off()
        self.select.on()
        self.select.off()
        # 3
        self.write_register(0x3a, 0x5a)
        # 4
        utime.sleep_ms(50)
        # 5
        self.read_pos()

        # SROM Download
        # As per page 23 of datasheet
        # 2
        self.write_register(0x10, 0x20)
        # 3
        self.write_register(0x13, 0x1d)
        # 4
        utime.sleep_ms(10)
        # 5
        self.write_register(0x13, 0x18)
        # 6
        self.download_srom(PROGMEM)
        # 7
        ID = int.from_bytes(self.read_register(0x2a), 'little')
        assert ID == 0x04, "bad SROM v={}".format(ID)
        # 8
        # Write 0x00 to Config2 register for wired mouse or 0x20 for wireless mouse design (Enable/Disable Rest mode)
        self.write_register(0x10, 0x00)

        # CONFIGURATION
        # set initial CPI resolution
        self.write_register(0x0f, 0x31)  # CPI setting=5000
        # set lift detection
        self.write_register(0x63, 0x03)  # Lift detection: +3mm

        self.select.off()

        utime.sleep_ms(10)

    def shut_down(self):
        """
        Perform the shut down sequence
        As per page 27 of datasheet
        """
        self.select.off()
        utime.sleep_ms(1)
        self.select.on()
        utime.sleep_ms(1)
        self.reset.on()
        utime.sleep_ms(60)
        self.read_pos()
        utime.sleep_ms(1)
        self.select.off()
        utime.sleep_ms(1)

        self.SPI.deinit()

    def download_srom(self, srom):
        self.select.on()
        # flip the MSB to 1:
        self.SPI.write((0x62 | 0x80) .to_bytes(1, 'little'))
        utime.sleep_us(15)
        for srom_byte in srom:
            self.SPI.write(srom_byte.to_bytes(1, 'little'))
            utime.sleep_us(15)

        self.select.off()

    def write_register_buff(self, addrs: bytes, data: bytes):
        """
        addrs < 128
        """
        # flip the MSB to 1:...
        self.select.on()
        self.SPI.write(addrs)
        self.SPI.write(data)
        utime.sleep_us(20)  # tSCLK-NCS for write operation
        self.select.off()
        utime.sleep_us(100)  # tSWW/tSWR (=120us) minus tSCLK-NCS. Could be shortened, but is looks like a safe lower bound

    def read_register_buff(self, addrs: bytes, buff: bytes):
        """
        addrs < 128
        """
        self.select.on()
        self.SPI.write(addrs)
        utime.sleep_us(100)  # tSRAD
        self.SPI.readinto(buff)
        utime.sleep_us(1)  # tSCLK-NCS for read operation is 120ns
        self.select.off()
        utime.sleep_us(19)  # tSRW/tSRR (=20us) minus tSCLK-NCS

    def read_pos_buff(self, buff):
        # write and read Motion register to lock the content of delta registers
        self.write_register_buff(b'\x02', b'\x81')
        self.read_register_buff(b'\x02', buff[0])

        self.read_register_buff(b'\x03', buff[1])
        self.read_register_buff(b'\x04', buff[0])
        self.read_register_buff(b'\x05', buff[3])
        self.read_register_buff(b'\x06', buff[2])
        # delta_x_H[0] + delta_x_L[1] + delta_y_H[2] + delta_y_L[3]


class MotionTimer(PMW3360DM):
    # Directly copied from Analog_input()
    def __init__(self, reset, sampling_rate=5000, event='motion'):
        PMW3360DM.__init__(self, SPI_type='SPI2', reset=reset)
        # Event generation variables
        self.event = event
        assign_ID(self)
        self.timestamp = fw.current_time
        # Data acqisition variables
        self.timer = pyb.Timer(available_timers.pop())
        self.sampling_rate = sampling_rate
        # Motion sensor variables
        self.motionBuffer = [bytearray(1), bytearray(1), bytearray(1), bytearray(1)]

    def record(self):
        self.power_up()
        self.timer.init(freq=self.sampling_rate)
        self.timer.callback(self._timer_ISR)

    def off(self):
        # Stop sampling analog input values.
        self.timer.deinit()
        self.shut_down()

    def _timer_ISR(self, t):
        # Read a sample to the buffer, update write index.
        self.read_pos_buff(self.motionBuffer)
        self.timestamp = fw.current_time
        interrupt_queue.put(self.ID)

    def _process_interrupt(self):
        # Put event generated by threshold crossing in event queue.
        fw.event_queue.put((self.timestamp, fw.event_typ, self.event_ID))

    def _initialise(self):
        self.event_ID = fw.events[self.event] if self.event in fw.events else False

    def _run_start(self):
        pass

    def _run_stop(self):
        pass
