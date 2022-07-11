from cooperative_multitasking import Tasks
from lora_states import NOT_JOINED, JOINING, JOINED, SENDING, SENT, RETRY
from asr6501 import ASR6501



gpio27 = Pin(27, Pin.OUT)
neopixels = NeoPixel(gpio27, 1)



    
def modem_state_changed():
    return modem.has_state_changed()

def start_join():
    print ("start_join")
    yellow()
    modem.send_join()
    tasks.when_then(modem_state_changed, end_join)
    
def end_join():
    print ("end_join")
    state = modem.get_state()
    
    print ("end_join, state="+str(state))
    if state == JOINING:
        tasks.when_then(modem_state_changed, end_join)
    elif state == JOINED:
        green()
        tasks.after(10000, start_send)
    elif state == NOT_JOINED:
        tasks.after(60000, start_join)
    else:
        raise NotImplementedError()
    
def start_send():
    global count
    
    print("start_send") 

    count += 1
    
    blue()
    modem.send_message(bytes(str(count), 'ASCII'), count % 29 == 1)  # message, confirmed
    
    tasks.when_then(modem_state_changed, end_send)

def end_send():
    print("end_send")
    
    state = modem.get_state()
    if state == SENDING:
        tasks.only_one_of(tasks.when_then(modem_state_changed, end_send), tasks.after(60000, assume_sent))  # workaround for AT+DTRX response lines
    elif state == SENT:
        magenta()
        tasks.after(300000, start_send)
    elif state == RETRY:
        red()
        tasks.after(300000, start_send)
    elif state == NOT_JOINED:
        red()
        tasks.after(300000, start_join)
    else:
        raise NotImplementedError()

def assume_sent():
    print("assue_sent")
    
    magenta()
    tasks.after(240000, start_send)


def yellow():
    neopixels[0] = (20, 20, 0)
    neopixels.write()

def green():
    neopixels[0] = (0, 25, 0)
    neopixels.write()

def blue():
    neopixels[0] = (0, 0, 25)
    neopixels.write()

def magenta():
    neopixels[0] = (20, 0, 20)
    neopixels.write()

def red():
    neopixels[0] = (25, 0, 0)
    neopixels.write()

red()
print ("Init Tasks")
tasks = Tasks()

print ("Configure UART (RX-19,TX-22")
uart2 = UART(2, tx=22, rx=19)
uart2.init(baudrate=115200, bits=8, parity=None, stop=1, txbuf=256, rxbuf=256)

print ("Configure ASR6501")

#Helium
modem = ASR6501(uart2, '6081F908B347B450', '6081F9994CD7478C', '08494BBE54CE153A0D5AA1B24508F7C6')  # DevEUI, AppEUI, AppKey as hex codes

# Internet of things
# modem = ASR6501(uart2, '70B3D57ED0046236', '0000000000000000', '32BA4962E4F5BCD1AA08713DBCEF2BEF')  # DevEUI, AppEUI, AppKey as hex codes
count = 0

tasks.now(start_join)

while tasks.available():
    tasks.run()
    


