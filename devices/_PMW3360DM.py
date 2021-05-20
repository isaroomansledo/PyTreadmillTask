import utime, machine
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
                 eventName: str,
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
        addrs = addrs.to_bytes(1, 'big')
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
        addrs = addrs.to_bytes(1, 'big')
        data = data.to_bytes(1, 'big')
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
        ID = int.from_bytes(self.read_register(0x2a), 'big')
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

    def download_srom(self, srom):
        self.select.on()
        # flip the MSB to 1:
        self.SPI.write((0x62 | 0x80) .to_bytes(1, 'big'))
        utime.sleep_us(15)
        for srom_byte in srom:
            self.SPI.write(srom_byte.to_bytes(1, 'big'))
            utime.sleep_us(15)

        self.select.off()

    def burst_read(self):
        """
        Based on Burst mode Page 22
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
        self.SPI.write(0x50 .to_bytes(1, 'big'))
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

    def read_register_buff(self, addrs: int, buff):
        """
        addrs < 128
        """
        # ensure MSB=0
        addrs = addrs & 0x7f
        addrs = addrs.to_bytes(1, 'big')
        self.select.on()
        self.SPI.write(addrs)
        utime.sleep_us(100)  # tSRAD
        self.SPI.readinto(buff)
        utime.sleep_us(1)  # tSCLK-NCS for read operation is 120ns
        self.select.off()
        utime.sleep_us(19)  # tSRW/tSRR (=20us) minus tSCLK-NCS
        return buff

    def read_pos_buff(self, buff):
        # write and read Motion register to lock the content of delta registers
        self.write_register(0x02, 0x01)
        self.read_register_buff(0x02, buff[0])

        self.read_register_buff(0x03, buff[1])
        self.read_register_buff(0x04, buff[0])
        self.read_register_buff(0x05, buff[3])
        self.read_register_buff(0x06, buff[2])
        # delta_x_H[0] + delta_x_L[1] + delta_y_H[2] + delta_y_L[3]


class MotionDetector(IO_object):
    # Directly copied from Analog_input(): MotionDetector(name, sampling_rate, reset, MT, event='motion')
    # Analog_input samples analog voltage from specified pin at specified frequency and can
    # stream data to continously to computer as well as generate framework events when 
    # voltage goes above / below specified value. The Analog_input class is subclassed
    # by other hardware devices that generate continous data such as the Rotory_encoder.
    # Serial data format for sending data to computer: 'A c i r l t k D' where:
    # A character indicating start of analog data chunk (1 byte)
    # c data array typecode (1 byte)
    # i ID of analog input  (2 byte)
    # r sampling rate (Hz) (2 bytes)
    # l length of data array in bytes (2 bytes)
    # t timestamp of chunk start (ms)(4 bytes)
    # k checksum (2 bytes)
    # D data array bytes (variable)

    def __init__(self, pin, name, sampling_rate, threshold=None, rising_event=None, 
                 falling_event=None, data_type='H'):
        if rising_event or falling_event:
            assert type(threshold) == int, 'Integer threshold must be specified if rising or falling events are defined.'
        assert data_type in ('b','B','h','H','l','L'), 'Invalid data_type.'
        assert not any([name == io.name for io in IO_dict.values() 
                        if isinstance(io, Analog_input)]), 'Analog inputs must have unique names.'
        if pin: # pin argument can be None when Analog_input subclassed.
            self.ADC = pyb.ADC(pin)
            self.read_sample = self.ADC.read
        self.name = name
        assign_ID(self)
        # Data acqisition variables
        self.timer = pyb.Timer(available_timers.pop())
        self.recording = False # Whether data is being sent to computer.
        self.acquiring = False # Whether input is being monitored.
        self.sampling_rate = sampling_rate
        self.data_type = data_type
        self.bytes_per_sample = {'b':1,'B':1,'h':2,'H':2,'l':4,'L':4}[data_type]
        self.buffer_size = max(4, min(256 // self.bytes_per_sample, sampling_rate//10))
        self.buffers = (array(data_type, [0]*self.buffer_size),array(data_type, [0]*self.buffer_size))
        self.buffers_mv = (memoryview(self.buffers[0]), memoryview(self.buffers[1]))
        self.buffer_start_times = array('i', [0,0])
        self.data_header = array('B', b'A' + data_type.encode() + 
            self.ID.to_bytes(2,'little') + sampling_rate.to_bytes(2,'little') + b'\x00'*8)
        # Event generation variables
        self.threshold = threshold
        self.rising_event = rising_event
        self.falling_event = falling_event
        self.timestamp = 0
        self.crossing_direction = False

    def _initialise(self):
        # Set event codes for rising and falling events.
        self.rising_event_ID  = fw.events[self.rising_event ] if self.rising_event  in fw.events else False
        self.falling_event_ID = fw.events[self.falling_event] if self.falling_event in fw.events else False
        self.threshold_active = self.rising_event_ID or self.falling_event_ID

    def _run_start(self):
        self.write_buffer = 0 # Buffer to write new data to.
        self.write_index  = 0 # Buffer index to write new data to. 
        if self.threshold_active: 
            self._start_acquisition()

    def _run_stop(self):
        if self.recording:
            self.stop()
        if self.acquiring:
            self._stop_acquisition()

    def _start_acquisition(self):
        # Start sampling analog input values.
        self.timer.init(freq=self.sampling_rate)
        self.timer.callback(self._timer_ISR)
        if self.threshold_active:
            self.above_threshold = self.read_sample() > self.threshold
        self.acquiring = True

    def record(self):
        # Start streaming data to computer.
        if not self.recording:
            self.write_index = 0  # Buffer index to write new data to. 
            self.buffer_start_times[self.write_buffer] = fw.current_time
            self.recording = True
            if not self.acquiring: self._start_acquisition()

    def stop(self):
        # Stop streaming data to computer.
        if self.recording:
            if self.write_index != 0:
                self._send_buffer(self.write_buffer, self.write_index)
            self.recording = False
            if not self.threshold_active: 
                self._stop_acquisition()

    def _stop_acquisition(self):
        # Stop sampling analog input values.
        self.timer.deinit()
        self.acquiring = False

    def _timer_ISR(self, t):
        # Read a sample to the buffer, update write index.
        self.buffers[self.write_buffer][self.write_index] = self.read_sample()
        if self.threshold_active:
            new_above_threshold = self.buffers[self.write_buffer][self.write_index] > self.threshold
            if new_above_threshold != self.above_threshold: # Threshold crossing.
                self.above_threshold = new_above_threshold
                if ((    self.above_threshold and self.rising_event_ID) or 
                    (not self.above_threshold and self.falling_event_ID)):
                        self.timestamp = fw.current_time
                        self.crossing_direction = self.above_threshold
                        interrupt_queue.put(self.ID)
        if self.recording:
            self.write_index = (self.write_index + 1) % self.buffer_size
            if self.write_index == 0: # Buffer full, switch buffers.
                self.write_buffer = 1 - self.write_buffer
                self.buffer_start_times[self.write_buffer] = fw.current_time
                stream_data_queue.put(self.ID)

    def _process_interrupt(self):
        # Put event generated by threshold crossing in event queue.
        if self.crossing_direction:
            fw.event_queue.put((self.timestamp, fw.event_typ, self.rising_event_ID))
        else:
            fw.event_queue.put((self.timestamp, fw.event_typ, self.falling_event_ID))

    def _process_streaming(self):
        # Stream full buffer to computer.
        self._send_buffer(1-self.write_buffer)

    def _send_buffer(self, buffer_n, n_samples=False):
        # Send specified buffer to host computer.
        n_bytes = self.bytes_per_sample*n_samples if n_samples else self.bytes_per_sample*self.buffer_size
        self.data_header[6:8]  = n_bytes.to_bytes(2,'little')
        self.data_header[8:12] = self.buffer_start_times[buffer_n].to_bytes(4,'little')
        checksum = sum(self.buffers_mv[buffer_n][:n_samples] if n_samples else self.buffers[buffer_n])
        checksum += sum(self.data_header[1:12])
        self.data_header[12:14] = checksum.to_bytes(2,'little')
        fw.usb_serial.write(self.data_header)
        if n_samples: # Send first n_samples from buffer.
            fw.usb_serial.send(self.buffers_mv[buffer_n][:n_samples])
        else: # Send entire buffer.
            fw.usb_serial.send(self.buffers[buffer_n])
