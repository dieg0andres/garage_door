import network
import urequests

from machine import Pin, Timer
from secrets import *
from time import sleep


SET_DOOR_STATUS = 'set_door_status'
OPEN = 'open'
CLOSED = 'closed'

led = Pin("LED", Pin.OUT)
sensor = Pin(6, Pin.IN, Pin.PULL_UP)

led.on()
door_status = -1

wlan = network.WLAN(network.STA_IF)


def connect_to_network():
    wlan.active(True)
    wlan.connect(SSID, PSSWRD)
    
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >=3:
            break
        max_wait -= 1
        print('Waiting for connection to WiFi...')
        sleep(1)
    
    if wlan.status() != 3:
        led.on()
        raise RuntimeError('network connection failed')

    else:
        print('connected to WiFi')
        status = wlan.ifconfig()
        print('ip = ' + status[0])
        led.off()


def reset_cb(timer):
    machine.reset()


def send_request_to_home_server(door_status):
    
    try:
        print('sending door status to home server...')
        response = urequests.get(HOME_SERVER + '/garage_door_controller/' + SET_DOOR_STATUS + '?door_status=' + door_status)

        if response.text == door_status:
            print('door_status received by home server :)')
        else:
            print('something went wrong, home server did not receive door status')        
        
        response.close()
    
    except:

        led.on()
        print('could not connect to home server (status =' + str(wlan.status()) + ')')
        if wlan.status() < 0 or wlan.status >= 3:
            print('trying to reconnect to WiFi...')
            wlan.disconnect()
            wlan.connect(SSID, PSSWRD)
            if wlan.status() == 3:
                print('connected to wifi')
                led.off()
            else:
                print('failed connecting to wifi')    


connect_to_network()
reset_timer = Timer()
reset_timer.init(period=1000*60*60*12, mode=Timer.PERIODIC, callback=reset_cb)

while True:
    
    sleep(5)
    led.on()
    sleep(0.5)
    led.off()
    
    previous_door_status = door_status
    reading = sensor.value()
    
    if reading == 1:
        door_status = CLOSED
    elif reading == 0:
        door_status = OPEN
    else:
        door_status = '_unknown_'
    
    if previous_door_status != door_status:
        print('door status chaged.  Door is: ', door_status)
        send_request_to_home_server(door_status)
          
    



