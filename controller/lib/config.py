from machine import Pin


door = Pin(21, Pin.OUT, value=0)
led = Pin("LED", Pin.OUT, value=1)


OPEN_CLOSE_DOOR = '/open_close_door'

RESPONSE_HEADER = 'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n'
FAIL = 'fail'
SUCCESS = 'success'

HOME_SERVER = 'http://192.168.86.32:8080'
