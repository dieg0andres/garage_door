import network
import time
import uasyncio as asyncio
import urequests as requests

from config import *
from machine import Timer
from secrets import *


wlan = network.WLAN(network.STA_IF)


def connect_to_network():   
    wlan.active(True)
    wlan.config(pm = 0xa11140)    # disable power-save mode
    wlan.connect(SSID, PSSWRD)

    # wait for connect or fail
    max_wait = 20
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('Waiting for connection...')
        time.sleep(2)

    # handle connection error
    if wlan.status() != 3:
        print('network connection failed', wlan.status())
        raise RuntimeError('network connection failed')
    else:
        print('RPi Pico W - Garage Door Controller connected to WiFi')
        status = wlan.ifconfig()
        print('ip = ' + status[0])
    
    asyncio.create_task(log_request('Connected_to_WiFi'))
    asyncio.create_task(log_request(status[0]))
    asyncio.create_task(send_ip())


def date_time():
    t = time.localtime()
    return ' ['+str(t[1])+'/'+str(t[2])+'/'+str(t[0])+' '+str(t[3])+':'+str(t[4])+':'+str(t[5])+'] '


async def log_request(msg):
    r = requests.get(HOME_SERVER + '/log/GARAGE_DOOR_CONTROLLER/'+msg)
    r.close()
    print('sent log request, message = ', msg)


def reset_pico_cb(timer):
    machine.reset()


async def send_ip():
    ip = wlan.ifconfig()[0]
    r = requests.get(HOME_SERVER + '/ip/GARAGE_DOOR_CONTROLLER/' + ip)
    r.close()
    print('sent ip', ip)


def send_ip_cb(timer):
    asyncio.create_task(send_ip())


async def serve_client(reader, writer):
    
    print('\nHome Server connected to RPi Pico W - Garage Door Controller')
    request_line = await reader.readline()
    print(date_time(), " The Request is: ", request_line)
    
    while await reader.readline() != b"\r\n":
        pass
    
    request = str(request_line)
    
    response = FAIL
        
    if OPEN_CLOSE_DOOR in request.split(' '):
        asyncio.create_task(toggle_switch())
        asyncio.create_task(log_request('Received_command_to_OPEN_CLOSE_DOOR'))
        response = SUCCESS
    
    writer.write(RESPONSE_HEADER)
    writer.write(response)
    
    await writer.drain()
    await writer.wait_closed()
    print('Home Server disconnected from RPi Pico W - Garage Door Controller')


def set_up_timers():
    send_ip_timer = Timer()
    reset_timer = Timer()
    
    # set up timer to send IP ADDR every 8 hours
    send_ip_timer.init(period=1*1000*60*60*8, mode=Timer.PERIODIC, callback=send_ip_cb)
    
    # set up timer to reset Pico W every 24 hours
    reset_timer.init(period=1*1000*60*60*24, mode=Timer.PERIODIC, callback=reset_pico_cb)


async def toggle_switch():
    door.toggle()
    await asyncio.sleep(0.85)
    door.toggle()
    print('garage door switch toggled')
    

async def main():

    print('Connecting to WiFi Network...')
    connect_to_network()
    
    print('Setting up Webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, '0.0.0.0', 8080))
    print('Webserver started on RPi Pico W')
    print('Waiting for client connection...')
    
    set_up_timers()
    
    while True:
        led.on()
        await asyncio.sleep(0.75)
        led.off()
        await asyncio.sleep(5)
        
try:
    asyncio.run(main())

finally:
    log_request('Server_down')
    asyncio.new_event_loop()