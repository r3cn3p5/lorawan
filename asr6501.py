# For M5Stack LoRaWAN Unit use
# uart = UART(2, tx=26, rx=32)
# uart.init(baudrate=115200, bits=8, parity=None, stop=1)

from lora_states import NOT_JOINED, JOINING, JOINED, CANNOT_JOIN, SENDING, SENT, RETRY, NOT_SENT
from utime import sleep_ms


class ASR6501:

    def __init__(self, uart, dev_eui, app_eui, app_key):
        self.uart = uart
        self.dev_eui = dev_eui
        self.app_eui = app_eui
        self.app_key = app_key
        self.line = None
        self.line_count = 0
        self.state = None
        self.next_state = None
        self._reset()
        self._write_configuration()


    def send_join(self):
        self._write_join()

    def send_message(self, message, confirmed):
        self._write_message(message, confirmed)

    def has_state_changed(self):
        return self._available()

    def get_state(self):
        if self.state == JOINING:
            self._read_join()
        elif self.state == SENDING:
            self._read_message()
        return self.state

    def _reset(self):
        self._write_read_command('IREBOOT', '0')
        self._write_read_command('ILOGLVL', '0')
        self._write_read_command('CGMI?')
        self._write_read_command('CGMM?')
        self._write_read_command('CGMR?')

    def _write_configuration(self):
        print ("_write_configuration")
        self._write_read_command('CJOINMODE', '0')
        self._write_read_command('CDEVEUI', self.dev_eui)
        self._write_read_command('CAPPEUI', self.app_eui)
        self._write_read_command('CAPPKEY', self.app_key)
        self._write_read_command('CADR', '1')
        self._write_read_command('CULDLMODE', '2')
        self._write_read_command('CCLASS', '2')
        self._write_read_command('CWORKMODE', '2')
        #self._write_read_command('CNBTRIALS', '0,5')
        #self._write_read_command('CNBTRIALS', '1,5')
        #self._write_read_command('CFREQLIST?')             # Not working
        self._write_read_command('CFREQBANDMASK', '0001')
        #self._write_read_command('CRXP', '0,0,869525000')  # >+CME ERROR:1< 
        #self._write_read_command('CTXP', '1')
        


    def _write_join(self):
        self._write_command('CJOIN', '1,1,10,8')
#        self._write_command('CJOIN', '1')
        self.state = JOININGAT
        self.line_count = 0

    def _write_message(self, message, confirmed):
       
        hex = ''
        for byte in message:
            hex += ('%02x' % byte)
            
        self._write_command('DTRX', ('1' if confirmed else '0') + ',1,' + str(len(message)) + ',' + hex)
        self.state = SENDING
        self.next_state = RETRY
        self.line_count = 0

    def _available(self):
        return self.uart.any() > 1

    def _read_join(self):
        
        self._read_line()
        
        if self._line_is_empty():
            self._clear_line()
        elif self._line_starts_with('+CJOIN:') and self._line_ends_with(':OK'):
            self._clear_line()
            self.state = JOINED
        elif self._line_starts_with('+CJOIN:') and self._line_ends_with(':FAIL'):
            self._clear_line()
            self.state = JOINING
        elif self._line_contains('ERROR'): # Not ssen
            self.state = NOT_JOINED

    def _read_message(self):
        
        self._read_line()
        
        if self._line_is_empty():
            self._clear_line()
        elif self._line_starts_with('AT+DTRX=') or self._line_starts_with('OK+SEND:') or self._line_starts_with('OK+SENT:') or self._line_starts_with('OK+RECV:'):
            self._clear_line()
            self.line_count += 1
            if self.line_count == 4:
                self.state = SENT
        elif self._line_starts_with('ERR+SEND:'):
            if self._line_ends_with(':0'):
                self.next_state = NOT_JOINED
        elif self._line_starts_with('ERR+SENT:'):
            self.state = self.next_state
        else:
            self.state = NOT_SENT

    def _write_read_command(self, command, argument = None):
        line = 'AT+'
        line += command
        if argument is not None:
            line += '='
            line += argument
   
        self._write_line(line)
        
        self._read_expected_line('OK')


    def _write_command(self, command, argument):
        line = 'AT+'
        line += command
        if argument is not None:
            line += '='
            line += argument
        self._write_line(line)

    def _write_line(self, line):
        print ("_write_line: >" + line + "<")
       
        self.uart.write(line)
        self.uart.write('\r\n')

    def _read_line(self):

        while self.uart.any() == 0:
            sleep_ms(30)
        self.line = str(self.uart.readline(), 'ASCII')[:-2]
        
        if not self._line_is_empty():
            print ("_read_line: (str)  >" + self.line + "< ")
            print ("_read_line: (hex) " + ":" .join("{:02x}".format(ord(c)) for c in self.line))


    def _read_expected_line(self, expected_line):
        self._read_line()
        while self._line_starts_with('ASR6501:') or self._line_starts_with('\r') or self._line_starts_with('[') or self._line_starts_with('AT+') or self._line_starts_with('+CGM') or self._line_is_empty():
            self._read_line()
        if not self._line_starts_with(expected_line) or self._line_contains('ERROR'):
            raise ValueError('expected ' + expected_line + ', but got >' + self.line + '<')
        self._clear_line()

    def _line_starts_with(self, part):
        return self.line.startswith(part)

    def _line_contains(self, part):
        return self.line.find(part) >= 0

    def _line_ends_with(self, part):
        return self.line.endswith(part)
        
    def _line_is_empty(self):
        return len(self.line) == 0

    def _clear_line(self):
        self.line = None
