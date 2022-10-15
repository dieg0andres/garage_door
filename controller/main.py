import network
import time
import uasyncio as asyncio
import urequests as requests

from config import *
from secrets import *


wlan = network.WLAN(network.STA_IF)


def date_time():
    t = time.localtime()
    return ' ['+str(t[1])+'/'+str(t[2])+'/'+str(t[0])+' '+str(t[3])+':'+str(t[4])+':'+str(t[5])+'] '


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
    
    log_request('Connected_to_WiFi')
    
    
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


async def toggle_switch():
    door.toggle()
    await asyncio.sleep(0.85)
    door.toggle()
    print('garage door switch toggled')
    

async def log_request(msg):
    r = requests.get(HOME_SERVER + '/log/GARAGE_DOOR_CONTROLLER/'+msg)
    r.close()

async def main():

    print('Connecting to WiFi Network...')
    connect_to_network()
    
    print('Setting up Webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, '0.0.0.0', 8080))
    print('Webserver started on RPi Pico W')
    print('Waiting for client connection...')
    
    while True:
        led.on()
        await asyncio.sleep(0.75)
        led.off()
        await asyncio.sleep(7)
        
try:
    asyncio.run(main())

finally:
    log_request('Server_down')
    asyncio.new_event_loop()