#
# USB serial communication for the Raspberry Pi Pico (RD2040) using the second RD2040
# thread/processor (written by Dorian Wiskow - Janaury 2021) 
#
from picographics import PicoGraphics, DISPLAY_TUFTY_2040
display = PicoGraphics(display=DISPLAY_TUFTY_2040)

from sys import stdin, exit
from _thread import start_new_thread
from utime import sleep
from pimoroni import Button
from attitude_indicator import AttitudeIndicator
import time
from math import degrees

# 
# global variables to share between both threads/processors
# 
bufferSize = 1024                 # size of circular buffer to allocate
buffer = [' '] * bufferSize       # circuolar incomming USB serial data buffer (pre fill)
bufferEcho = True                 # USB serial port echo incooming characters (True/False) 
bufferNextIn, bufferNextOut = 0,0 # pointers to next in/out character in circualr buffer
terminateThread = False           # tell 'bufferSTDIN' function to terminate (True/False)
#
# bufferSTDIN() function to execute in parallel on second Pico RD2040 thread/processor
#
def bufferSTDIN():
    global buffer, bufferSize, bufferEcho, bufferNextIn, terminateThread
    
    while True:                                 # endless loop
        if terminateThread:                     # if requested by main thread ...
            break                               #    ... exit loop
        buffer[bufferNextIn] = stdin.read(1)    # wait for/store next byte from USB serial
        if bufferEcho:                          # if echo is True ...
            print(buffer[bufferNextIn], end='') #    ... output byte to USB serial
        bufferNextIn += 1                       # bump pointer
        if bufferNextIn == bufferSize:          # ... and wrap, if necessary
            bufferNextIn = 0
#
# instantiate second 'background' thread on RD2040 dual processor to monitor and buffer
# incomming data from 'stdin' over USB serial port using ‘bufferSTDIN‘ function (above)
#
bufferSTDINthread = start_new_thread(bufferSTDIN, ())

#
# function to check if a byte is available in the buffer and if so, return it
#
def getByteBuffer():
    global buffer, bufferSize, bufferNextOut, bufferNextIn
    
    if bufferNextOut == bufferNextIn:           # if no unclaimed byte in buffer ...
        return ''                               #    ... return a null string
    n = bufferNextOut                           # save current pointer
    bufferNextOut += 1                          # bump pointer
    if bufferNextOut == bufferSize:             #    ... wrap, if necessary
        bufferNextOut = 0
    return (buffer[n])                          # return byte from buffer

#
# function to check if a line is available in the buffer and if so return it
# otherwise return a null string
#
# NOTE 1: a line is one or more bytes with the last byte being LF (\x0a)
#      2: a line containing only a single LF byte will also return a null string
#
def getLineBuffer():
    global buffer, bufferSize, bufferNextOut, bufferNextIn

    if bufferNextOut == bufferNextIn:           # if no unclaimed byte in buffer ...
        return ''                               #    ... RETURN a null string

    n = bufferNextOut                           # search for a LF in unclaimed bytes
    while n != bufferNextIn:
        if buffer[n] == '\x0a':                 # if a LF found ... 
            break                               #    ... exit loop ('n' pointing to LF)
        n += 1                                  # bump pointer
        if n == bufferSize:                     #    ... wrap, if necessary
            n = 0
    if (n == bufferNextIn):                     # if no LF found ...
            return ''                           #    ... RETURN a null string

    line = ''                                   # LF found in unclaimed bytes at pointer 'n'
    n += 1                                      # bump pointer past LF
    if n == bufferSize:                         #    ... wrap, if necessary
        n = 0

    while bufferNextOut != n:                   # BUILD line to RETURN until LF pointer 'n' hit
        
        if buffer[bufferNextOut] == '\x0d':     # if byte is CR
            bufferNextOut += 1                  #    bump pointer
            if bufferNextOut == bufferSize:     #    ... wrap, if necessary
                bufferNextOut = 0
            continue                            #    ignore (strip) any CR (\x0d) bytes
        
        if buffer[bufferNextOut] == '\x0a':     # if current byte is LF ...
            bufferNextOut += 1                  #    bump pointer
            if bufferNextOut == bufferSize:     #    ... wrap, if necessary
                bufferNextOut = 0
            break                               #    and exit loop, ignoring (i.e. strip) LF byte
        line = line + buffer[bufferNextOut]     # add byte to line
        bufferNextOut += 1                      # bump pointer
        if bufferNextOut == bufferSize:         #    wrap, if necessary
            bufferNextOut = 0
    return line                                 # RETURN unclaimed line of input




kInitModule = const(0)
kSetModule = const(1)
kSetPin = const(2)
kSetStepper = const(3)
kSetServo = const(4)
kStatus = const(5) # Command to report status
kEncoderChange = const(6)
kButtonChange = const(7)
kStepperChange = const(8)
kGetInfo = const(9)
kInfo = const(10)
kSetConfig = const(11)
kGetConfig = const(12)
kResetConfig = const(13)
kSaveConfig = const(14)
kConfigSaved = const(15)
kActivateConfig = const(16)
kConfigActivated = const(17)
kSetPowerSavingMode = const(18)
kSetName = const(19)
kGenNewSerial = const(20)
kResetStepper = const(21)
kSetZeroStepper = const(22)
kTrigger = const(23)
kResetBoard = const(24)
kSetLcdDisplayI2C = const(25)
kSetModuleBrightness = const(26)
kSetShiftRegisterPins = const(27)
kAnalogChange = const(28)
kInputShifterChange = const(29)
kDigInMuxChange = const(30)

# device types
kButton = const(1)
kEncoderSingleDetent = const(2) # (retained for backwards compatibility, use Encoder for new configs)
kOutput = const(3) # Note - single pin analog value outputs
kLedModule = const(4)
kStepperDeprecated = const(5)
kServo = const(6)
kLcdDisplay = const(7)
kEncoder = const(8)
kStepper = const(9)
kShiftRegister = const(10)
kAnalogInput = const(11)
kInputShiftRegister = const(12)
kMultiplexerDriver = const(13) #  Not a proper device, but index required for update events
kInputMultiplexer = const(15)

WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
def printMessage(msg):
    if len(msg.strip()) == 0:
        return
    global display, BLACK, WHITE
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text(msg, 0, 0, 320, 4)
    display.update()
printMessage("Starting MobiFlight")

cmdLine = ""
lastCmd = ""
def processNewCharacter(char):
    global cmdLine, lastCmd
    if char == ";":
        handleMessage(cmdLine)
        lastCmd = cmdLine
        cmdLine = ""
    else:
        if char != "\n":
            cmdLine += char
            
def sendMessage(key, args):
    cmd = str(key)
    for arg in args:
        cmd += "," + str(arg)
    cmd += ";"
    print(cmd)

commands = {}
def addHandler(code, handler):
    global commands
    commands[code] = handler
    
def cmdGetConfig(arguments):
    sendMessage(kInfo, ["1.7.ButtonA:7.32.16.1.Pitch:7.33.16.1.Bank:"])
addHandler(kGetConfig, cmdGetConfig)

def cmdGetInfo(arguments):
    sendMessage(kInfo, ["MobiFlight Tufty2040","MobiFlight Tufty2040","SN-752-f99","0.0.1"])
addHandler(kGetInfo, cmdGetInfo)
    
def cmdSetLcdDisplayI2C(arguments):
    global display, WHITE, BLACK
    address = arguments[0]
    text = arguments[1]
    printMessage(text)
#addHandler(kSetLcdDisplayI2C, cmdSetLcdDisplayI2C)
    
variables = {0:"0", 1:"0"}
def cmdSetVariable(arguments):
    print("*", arguments, "*")
    variables[int(arguments[0])] = arguments[1]
addHandler(kSetLcdDisplayI2C, cmdSetVariable)
    
def handleMessage(message):
    global commands
    parts = message.split(",")
    if len(parts) > 0:
        key = int(parts[0])
        if key in commands:
            commands[key](parts[1:])
        

print (Button)
button_a = Button(7, invert=False)
button_a_pressed = False
def handleButtons():
    global button_a, button_a_pressed
    if button_a.is_pressed != button_a_pressed:
        change = int(not button_a.is_pressed)
        sendMessage(kButtonChange, {"ButtonA", change})
        button_a_pressed = button_a.is_pressed
    
        
print("Starting MobiFlight")    

#
# main program begins here ...
#
# set 'inputOption' to either  one byte ‘BYTE’  OR one line ‘LINE’ at a time. Remember, ‘bufferEcho’
# determines if the background buffering function ‘bufferSTDIN’ should automatically echo each
# byte it receives from the USB serial port or not (useful when operating in line mode when the
# host computer is running a serial terminal program)
#
# start this MicroPython code running (exit Thonny with code still running) and then start a
# serial terminal program (e.g. putty, minicom or screen) on the host computer and connect
# to the Raspberry Pi Pico ...
#
#    ... start typing text and hit return.
#
#    NOTE: use Ctrl-C, Ctrl-C, Ctrl-D then Ctrl-B on in the host computer terminal program 
#           to terminate the MicroPython code running on the Pico 
#
ai = AttitudeIndicator(display)
pitch = 0
bank = 0
try:
    inputOption = 'BYTE'                    # get input from buffer one BYTE or LINE at a time
    while True:

        if inputOption == 'BYTE':           # NON-BLOCKING input one byte at a time
            buffCh = getByteBuffer()        # get a byte if it is available?
            if buffCh:                      # if there is...
                # print (buffCh, end='')      # ...print it out to the USB serial port
                processNewCharacter(buffCh)

        elif inputOption == 'LINE':         # NON-BLOCKING input one line at a time (ending LF)
            buffLine = getLineBuffer()      # get a line if it is available?
            if buffLine:                    # if there is...
                print (buffLine)            # ...print it out to the USB serial port
                
        # Check hardware
        handleButtons()

        #sleep(0.1)
        
        #start = time.ticks_us()
        
        try:
            pitch = float(variables[0].strip())
            bank = float(variables[1].strip())
        except:
            a = 1
        ai.draw(bank, pitch)
        display.set_pen(WHITE)
        display.text(lastCmd, 0, 0, 320, 2)
        display.update()
        
        #print(time.ticks_diff(time.ticks_us(), start))
        #time.sleep_us(1)

except KeyboardInterrupt:                   # trap Ctrl-C input
    terminateThread = True                  # signal second 'background' thread to terminate 
    exit()
except BaseException as err:
    terminateThread = True
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text(str(err), 0, 0, 320, 1)
    display.update()
    exit()