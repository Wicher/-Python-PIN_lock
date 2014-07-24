# ************************************************************
# *    _|_|_|_|_|  _|_|_|  _|_|_|_|  _|_|_|_|_|    _|_|      *
# *        _|        _|    _|            _|      _|    _|    *
# *        _|        _|    _|_|_|        _|      _|    _|    *
# *        _|        _|    _|            _|      _|    _|    *
# *        _|      _|_|_|  _|_|_|_|      _|        _|_|      *
# *                                                          *
# ************************************************************
# * Copyright 2014 Tieto                                     *
# * Author: bartosz.zawieja@tieto.com                        *
# * All rights, including trade secret rights, reserved.     *
# ************************************************************
import sys
import os 
import serial
import time
import getopt

timeout = 2

#Default PIN and PUK code for Anritsu cards
PIN_code = 1111
PUK_code = 11111111

modem_activate = "adb root && timeout 2 && adb remount && adb shell setprop persist.usb.eng 1 && adb shell setprop sys.usb.config mtp,adb && timeout 3"

class AT:
    #COMMANDS
    CPIN_check  = 'AT+CPIN?\r\n'
    SIM_enable  = 'AT+CFUN=1\r\n'
    SIM_disable = 'AT+CFUN=0\r\n'
    PIN_enter   = "AT+CPIN=" + str(PIN_code) + "\r\n"
    PUK_enter   = "AT+CPIN=" + str(PUK_code) + "," + str(PIN_code) + "\r\n"
    
    #RESPONSES
    OK          = 'OK\r\n'
    CPIN_ready  = '+CPIN: READY\r\n'
    lock_PIN    = '+CPIN: SIM PIN\r\n'
    lock_PUK    = '+CPIN: SIM PUK\r\n'
    lock_PIN2   = '+CPIN: SIM PIN2\r\n'
    lock_PUK2   = '+CPIN: SIM PUK2\r\n'
    lock_PH_SIM = '+CPIN: PH-SIM PIN\r\n'
    lock_PH_NT  = '+CPIN: PH-NET PIN\r\n'

def main(argv):

    connection = serial.Serial()
    connection.baudrate = 115200
    connection.timeout = 3

    if argv:
        try:
            opts, args = getopt.getopt(argv, "hmdc:lbpsr", ["help", "modem", "default", "comport=", "lock", "block", "pin", "state",  "reset"])
        except getopt.GetoptError:
            print "Invalid argument(s)"
            sys.exit(2)
        for opt, arg in opts[:1]:
            if opt in ("-h", "--help"):
                help()
                sys.exit()
            elif opt in ("-m", "--modem"):
                os.system(modem_activate)
                sys.exit()
            elif opt in ("-d", "--default"):
                default()
                sys.exit()
            elif opt in ("-c", "--comport"):
                connect(connection,arg)
                break
            else:
                print "No com port specified"
                assert False, "No com port specified"

        for opt, arg in opts[1:]:
            if opt in ("-l", "--lock"):
                pin_lock(connection)   
            elif opt in ("-b", "--block"):
                puk_block(connection)
            elif opt in ("-p", "--pin"):
                pin_enter(connection)    
            elif opt in ("-s", "--state"):
                pin_state(connection)  
            elif opt in ("-r", "--reset"):
                pin_reset(connection)
            else:
                print "No com port specified"
                assert False, "No com port specified"    

    else:
        print "Input port number or name: ",
        port = raw_input().upper()
        pin_lock(connection,port)

#============================== CONNECTION ====================================
def connect(connection,port):
    if "COM" in port:
        connection.port = port
    else:
        connection.port = "COM" + port
    connection.open()
    if connection.isOpen():
        print "Connected at " + connection.name + " port" 
    else: 
        print "Cannot connect to" + connection.name + " port" 
        sys.exit()

#============================== PIN LOCK ======================================
def pin_lock(connection):
    if not connection.isOpen():
        connection.open()
    seq = []
    leave = False
    connection.write(AT.CPIN_check)
    while True:
        seq.append(connection.readline())
        if AT.CPIN_ready in seq:
            seq = []
            connection.write(AT.SIM_disable)
            time.sleep(1)
            print "Locking phone..."
            connection.write(AT.SIM_enable)
            time.sleep(1)
            connection.write(AT.CPIN_check)
            end_time = time.time() + timeout
            while True:
                if time.time() >= end_time:
                    print "Timed Out"
                    sys.exit(1)
                else:
                    seq.append(connection.readline())
                    if AT.lock_PIN in seq:
                        print "Device is locked"
                        leave = True
                        break
        elif AT.OK in seq:
            print "Device is locked"
            break
         
        if leave is True:
            break
    connection.close()

#============================== PUK BLOCK =====================================
def puk_block(connection):
    pass





#============================== PIN ENTER =====================================
def pin_enter(connection):
    if not connection.isOpen():
        connection.open()
    seq = []
    leave = False
    connection.write(AT.CPIN_check)
    while True:
        seq.append(connection.readline())
        if AT.lock_PIN in seq:
            seq = []
            connection.write(AT.PIN_enter)
            time.sleep(1)
            connection.write(AT.CPIN_check)
            end_time = time.time() + timeout
            while True:
                if time.time() >= end_time:
                    print "Timed Out"
                    sys.exit(1)
                else:
                    seq.append(connection.readline())
                    if AT.CPIN_ready in seq:
                        print "Device is unlocked"
                        leave = True
                        break
        elif AT.CPIN_ready in seq:
            print "Device is not PIN locked"
            break
        elif AT.lock_PUK in seq:
            print "Device is PUK locked"
            break
        elif AT.OK in seq:
            break
         
        if leave is True:
            break
    connection.close() 

#============================== PIN STATE =====================================
def pin_state(connection):
    if not connection.isOpen():
        connection.open()
    seq = []
    connection.write(AT.CPIN_check)
    end_time = time.time() + timeout
    while True:
        if time.time() >= end_time:
            print "Timed Out"
            sys.exit(1)
        else:
            seq.append(connection.readline())
            if AT.CPIN_ready in seq:
                print "Device is unlocked"
                break
            elif AT.lock_PIN in seq:
                print "Device is PIN locked";
                break
            elif AT.lock_PUK in seq:
                print "Device is PUK locked";
                break
            elif AT.lock_PIN2 in seq:
                print "Device is PIN2 locked"; 
                break
            elif AT.lock_PUK2 in seq:
                print "Device is PUK2 locked";
                break
            elif AT.lock_PH_SIM in seq:
                print "SIM lock is required";
                break
            elif AT.lock_PH_NT in seq:
                print "Network personalisation is required";
                break
    connection.close() 

#============================== PIN RESET =====================================
def pin_reset(connection):
    if not connection.isOpen():
        connection.open()
    seq = []
    leave = False
    connection.write(AT.CPIN_check)
    while True:
        seq.append(connection.readline())
        if AT.lock_PUK in seq:
            seq = []
            connection.write(AT.PUK_enter)
            time.sleep(1)
            connection.write(AT.CPIN_check)
            end_time = time.time() + timeout
            while True:
                if time.time() >= end_time: 
                    print "Timed Out"
                    sys.exit(1)
                else:
                    seq.append(connection.readline())
                    if AT.CPIN_ready in seq:
                        print "Device is unlocked"
                        leave = True
                        break
        elif AT.OK in seq:
            print "Device is not PUK locked"
            break

        if leave is True:
            break
    connection.close()   

#============================== HELP ==========================================
def help():
    print "========== HELP =========="
    print "syntax: \n \t PIN_lock.py [option] ([parameter]...) \n \t"
    print "Support for parameter chaining (direction from left to right)"
    print "Option:"
    print "  -h --help      Show this help message and exit"
    print "  -m --modem     Activate modem and exit"
    print "  -d --default   Print default PIN and PUK codes"
    print "  -c --comport   Connect to specified COM port"
    print "Parameter:"
    print "  -l --lock      PIN lock device"
    print "  -b --block     PUK block device"
    print "  -p --pin       Enter default PIN code"
    print "  -s --state     Get SIM lock state"
    print "  -r --reset     Reset the PUK locked device with default PIN code"

#============================== CODES =========================================
def default():
    print "Default PIN code = " + str(PIN_code)
    print "Default PUK code = " + str(PUK_code)

#============================== MAIN ==========================================
if __name__ == "__main__":
    main(sys.argv[1:])