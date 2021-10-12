import pyb, utime, machine, math
from array import array

from pyControl.hardware import *
from devices.PMW3360DM_srom_0x04 import PROGMEM

def twos_comp(val, bits=16):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)         # compute negative value
    return val                          # return positive value as is


def endian_swap(val: int):
    "Swaps byte order. Tested for 2-byte input"
    return ((val & 0x00ff) << 8) | ((val & 0xff00) >> 8)

#1st Class: General class for a mouse sensor. It is the same code as Mostafa's previous code

class PMW3360DM():
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
        SPIparams = {'baudrate': 1000000, 'polarity': 1, 'phase': 1,
                     'bits': 8, 'firstbit': machine.SPI.MSB}
        if '1' in SPI_type:
            self.SPI = machine.SPI(1, **SPIparams)
            self.select = Digital_output(pin='W7', inverted=True)

        elif '2' in SPI_type:
            self.SPI = machine.SPI(2, **SPIparams)
            self.select = Digital_output(pin='W45', inverted=True)

        elif 'soft' in SPI_type.lower():  # not tested
            self.SPI = machine.SoftSPI(sck=machine.Pin(id=SCK, mode=machine.Pin.OUT, pull=machine.Pin.PULL_DOWN),
                                       mosi=machine.Pin(id=MO, mode=machine.Pin.OUT, pull=machine.Pin.PULL_DOWN),
                                       miso=machine.Pin(id=MI, mode=machine.Pin.IN), **SPIparams)
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

        delta_x = int.from_bytes(delta_x, 'little')
        delta_y = int.from_bytes(delta_y, 'little')

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
        self.write_register(0x0f, 0x00)  # CPI setting 0x31=5000; 0x00=100
        # set lift detection
        self.write_register(0x63, 0x03)  # Lift detection: +3mm
        self.CPI = int.from_bytes(self.read_register(0x0f), 'little') * 100 + 100

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

    def burst_read(self):
        """
        Based on Burst mode Page 22 [not tested]
        reads 12 bytes:
        BYTE[00] = Motion    = if the 7th bit is 1, a motion is detected.
            ==> 7 bit: MOT (1 when motion is detected)
            ==> 3 bit: 0 when chip is on surface / 1 when off surface
        BYTE[01] = Observation
        BYTE[02] = Delta_X_L = dx (LSB)
        BYTE[03] = Delta_X_H = dx (MSB)
        BYTE[04] = Delta_Y_L = dy (LSB)
        BYTE[05] = Delta_Y_H = dy (MSB)
        ...
        """
        # 1
        self.write_register(0x50, 0x00)
        # 2
        self.select.on()
        # 3
        self.SPI.write(0x50 .to_bytes(1, 'little'))
        # 4
        utime.sleep_us(35)  # wait for tSRAD_MOTBR
        # 5
        data = self.SPI.read(6)
        # 6
        self.select.off()
        utime.sleep_us(2)

        delta_x = (data[3] << 8) | data[2]
        delta_y = (data[5] << 8) | data[4]

        delta_x = twos_comp(delta_x)
        delta_y = twos_comp(delta_y)

        return delta_x, delta_y

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

#2nd Class: Class that creates a channel to send data to the computer

class one_analog_channel(Analog_input):

    def __init__(self,name,sampling_rate,threshold):
        self.sampling_rate = sampling_rate
       
        #Parent:
        Analog_input.__init__(self, pin=None,name=name,sampling_rate=int(sampling_rate),
                              threshold=threshold, rising_event=None, falling_event=None, data_type='l')
        self.crossing_direction = True  # to conform to the Analog_input syntax
        self.threshold_active = True
        #Overrides my analog input. I don't want a timer for each channel but a common timer instantiated in the super class.
        self.timer.deinit()
       
       
     #This function will send the information to the computer. Data is the xy_mix integer.
    def send_info(self, data,delta_x, delta_y):
        # Put a sample in the buffer, update write index.
        self.buffers[self.write_buffer][self.write_index] = data

        if self.threshold_active:  #It is always active when there is motion. It has been set to true in the initialise function
            if delta_x**2 + delta_y**2 >= self.threshold:
                self.timestamp = fw.current_time
                interrupt_queue.put(self.ID)
        if self.recording:
            self.write_index = (self.write_index + 1) % self.buffer_size
        if self.write_index == 0: # Buffer full, switch buffers.
            self.write_buffer = 1 - self.write_buffer
            self.buffer_start_times[self.write_buffer] = fw.current_time
            stream_data_queue.put(self.ID)

   
#3rd class: Super class, gets data from the 2 sensors and links it to the 2 channels so the computer can get the data.
class two_sensors (IO_object):
    def __init__(self,name1,name2,reset, threshold=10, sampling_rate=300, event='motion'):
    #Creating 2 sensors
        self.name1 = name1
        self.name2 = name2
        self.sampling_rate = sampling_rate
        self.sensor_1 = PMW3360DM(SPI_type='SPI2', eventName='', reset=reset)
        self.sensor_1.power_up()
        self.sensor_2 = PMW3360DM(SPI_type='SPI1', eventName='', reset=reset)
        self.sensor_2.power_up()
        self.threshold = threshold
        self.channel_1 = one_analog_channel(name1,sampling_rate,self._threshold)
        self.channel_2 = one_analog_channel(name2,sampling_rate,self._threshold)
        self.channel_1.recording = False
        self.channel_1.acquiring = False
        self.channel_2.recording = False
        self.channel_2.acquiring = False
       
         #Common timer:
        self.common_timer = pyb.Timer(available_timers.pop())

    #Storing data from sensors:
      # Motion sensor1 variables
        self.motionBuffer1 = bytearray(4)
        self.motionBuffer1_mv = memoryview(self.motionBuffer1)
        self.delta_x1_L_mv = self.motionBuffer1_mv[1:2]
        self.delta_x1_H_mv = self.motionBuffer1_mv[0:1]
        self.delta_y1_L_mv = self.motionBuffer1_mv[2:3]
        self.delta_y1_H_mv = self.motionBuffer1_mv[3:]
       
        self.delta_x1_mv = self.motionBuffer1_mv[:2]  # byte order is reversed
        self.delta_y1_mv = self.motionBuffer1_mv[2:]
        self.xy1_mix_mv = self.motionBuffer1_mv[1:3]
        self.delta_x1, self.delta_y1 = 0, 0
        self._delta_x1, self._delta_y1 = 0, 0


        # Motion sensor1 variables
        self.motionBuffer2 = bytearray(4)
        self.motionBuffer2_mv = memoryview(self.motionBuffer2)
        self.delta_x2_L_mv = self.motionBuffer2_mv[1:2]
        self.delta_x2_H_mv = self.motionBuffer2_mv[0:1]
        self.delta_y2_L_mv = self.motionBuffer2_mv[2:3]
        self.delta_y2_H_mv = self.motionBuffer2_mv[3:]
       
        self.delta_x2_mv = self.motionBuffer2_mv[:2]  # byte order is reversed
        self.delta_y2_mv = self.motionBuffer2_mv[2:]
        self.xy2_mix_mv = self.motionBuffer2_mv[1:3]
        self.delta_x2, self.delta_y2 = 0, 0
        self._delta_x2, self._delta_y2 = 0, 0

    @property
    def threshold(self):
        "return the value in cms"
        return math.sqrt(self._threshold) / self.sensor_1.CPI * 2.54

    @threshold.setter
    def threshold(self, new_threshold):    
        self._threshold = int((new_threshold / 2.54 * self.sensor_1.CPI)**2)
        self.reset_delta()
       
    def reset_delta(self):
    #reset the accumulated position data
        self.delta_x1, self.delta_y1 = 0, 0
        self.delta_x2, self.delta_y2 = 0, 0
       
    def read_sample(self):
     #Mouse sensor 1:
        self.sensor_1.write_register_buff(b'\x82', b'\x01')
        self.sensor_1.read_register_buff(b'\x02', self.delta_x1_H_mv)
        self.sensor_1.read_register_buff(b'\x03', self.delta_x1_L_mv)
        self.sensor_1.read_register_buff(b'\x04', self.delta_x1_H_mv)
        self.sensor_1.read_register_buff(b'\x05', self.delta_y1_L_mv)
        self.sensor_1.read_register_buff(b'\x06', self.delta_y1_H_mv)
        self._delta_y1 = int.from_bytes(self.delta_y1_mv, 'little')
        self._delta_x1 = endian_swap(int.from_bytes(self.delta_x1_mv, 'little'))

        self.delta_y1 += twos_comp(self._delta_y1)
        self.delta_x1 += twos_comp(self._delta_x1)

         #Mouse sensor 1:
        self.sensor_2.write_register_buff(b'\x82', b'\x01')
        self.sensor_2.read_register_buff(b'\x02', self.delta_x2_H_mv)
        self.sensor_2.read_register_buff(b'\x03', self.delta_x2_L_mv)
        self.sensor_2.read_register_buff(b'\x04', self.delta_x2_H_mv)
        self.sensor_2.read_register_buff(b'\x05', self.delta_y2_L_mv)
        self.sensor_2.read_register_buff(b'\x06', self.delta_y2_H_mv)
        self._delta_y2 = int.from_bytes(self.delta_y2_mv, 'little')
        self._delta_x2 = endian_swap(int.from_bytes(self.delta_x2_mv, 'little'))

        self.delta_y2 += twos_comp(self._delta_y2)
        self.delta_x2 += twos_comp(self._delta_x2)
   
    def timer_ISR(self,t):
        self.read_sample()
        self.channel_1.send_info(int.from_bytes(self.xy1_mix_mv,'little'),self.delta_x1,self.delta_y1) #Sends all of the data integers recorded by the sensor through the channel to the computer
        self.channel_2.send_info(int.from_bytes(self.xy2_mix_mv,'little'),self.delta_x2,self.delta_y2) #Sends all of the data integers recorded by the sensor through the channel to the computer
        self.reset_delta()

    def _initialise(self):
        pass

    def _run_start(self):
        pass
   
    def _run_stop(self):
        if self.channel_1.recording:
            self.channel_1.stop()
        if self.channel_1.acquiring:
            self._stop_acquisition()
        if self.channel_2.recording:
            self.channel_2.stop()
        if self.channel_2.acquiring:
            self._stop_acquisition()

    def record(self):
        # Start streaming data to computer.
        self.channel_1.write_buffer = 0
        self.channel_1.write_index = 0  # Buffer index to write new data to.
        self.channel_1.buffer_start_times[self.channel_1.write_buffer] = fw.current_time
        self.channel_2.buffer_start_times[self.channel_2.write_buffer] = fw.current_time
        self.channel_1.recording = True
        self.channel_2.recording = True
        if not self.channel_1.acquiring: self._start_acquisition()

    def _stop_acquisition(self):
        # Stop sampling analog input values.
        self.common_timer.deinit()
        self.sensor_1.shut_down()
        self.sensor_2.shut_down()
        self.channel_1.acquiring = False
        self.channel_2.acquiring = False

    def _start_acquisition(self):
        # Start sampling analog input values.
        self.common_timer.init(freq=self.sampling_rate)
        self.common_timer.callback(self.timer_ISR)
        self.channel_1.acquiring = True
        self.channel_2.acquiring = True