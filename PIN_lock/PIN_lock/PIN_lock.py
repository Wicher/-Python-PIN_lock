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
IMSI = 0

#PIN and PUK codes
PIN = 0
PUK = 0
PIN_def = 1111
PUK_def = 11111111

class AT:
    #COMMANDS
    IMSI_check  = 'AT+CIMI\r\n'
    CPIN_check  = 'AT+CPIN?\r\n'
    SIM_enable  = 'AT+CFUN=1\r\n'
    SIM_disable = 'AT+CFUN=0\r\n'
    PIN_enter   = "AT+CPIN=" + str(PIN) + "\r\n"
    PUK_enter   = "AT+CPIN=" + str(PUK) + "," + str(PIN) + "\r\n"
    
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
            opts, args = getopt.getopt(argv, "hmc:lbpsr", ["help", "modem", "comport=", "lock", "block", "pin", "state",  "reset"])
        except getopt.GetoptError:
            print "Invalid argument(s)"
            sys.exit(2)
        for opt, arg in opts[:1]:
            if opt in ("-h", "--help"):
                Options.help()
                sys.exit()
            elif opt in ("-m", "--modem"):
                Options.activate_modem()
                sys.exit()
            elif opt in ("-c", "--comport"):
                Options.connect(connection,arg)
                Methods.importPIN(connection,argv)
                break
            else:
                print "No com port specified"
                assert False, "No com port specified"

        for opt, arg in opts[1:]:
            if opt in ("-l", "--lock"):
                Commands.pin_lock(connection)   
            elif opt in ("-b", "--block"):
                Commands.puk_block(connection)
            elif opt in ("-p", "--pin"):
                Commands.pin_enter(connection)    
            elif opt in ("-s", "--state"):
                Commands.pin_state(connection)  
            elif opt in ("-r", "--reset"):
                Commands.pin_reset(connection)
            else:
                print "No com port specified"
                assert False, "No com port specified"    
    else:
        print "Input port number or name: ",
        port = raw_input().upper()
        pin_lock(connection,port)

###############################################################################
#                               OPTIONS                                       #
###############################################################################
class Options:
    
    modem_activate = "adb root && timeout 2 && adb remount && adb shell setprop persist.usb.eng 1 && adb shell setprop sys.usb.config mtp,adb && timeout 3"

    #============================== HELP ======================================
    @staticmethod
    def help():
        print "========== HELP =========="
        print "syntax: \n \t PIN_lock.py [option] ([command]...) \n \t"
        print "Support for parameter chaining (direction from left to right) \n"
        print "Option:"
        print "  -h --help      Show this help message and exit"
        print "  -m --modem     Activate modem and exit"
        print "  -C --codes     Print PIN and PUK codes"
        print "  -c --comport   Connect to specified COM port"
        print "Command:"
        print "  -l --lock      PIN lock device"
        print "  -b --block     PUK block device"
        print "  -p --pin       Enter default PIN code"
        print "  -s --state     Get SIM lock state"
        print "  -r --reset     Reset the PUK locked device with default PIN code"

    #============================== MODEM =====================================
    @staticmethod
    def activate_modem():
        os.system(modem_activate)

    #============================== CONNECTION ================================
    @staticmethod
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

###############################################################################
#                               COMMANDS                                      #
###############################################################################
class Commands:
    #============================== PIN LOCK ==================================
    @staticmethod
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

    #============================== PUK BLOCK =================================
    @staticmethod
    def puk_block(connection):
        pass

    #============================== PIN ENTER =================================
    @staticmethod
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

    #============================== PIN STATE =================================
    @staticmethod
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

    #============================== PIN RESET =================================
    @staticmethod
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

###############################################################################
#                               METHODS                                       #
###############################################################################
class Methods:
    
    fName = "PIN.txt"

    #============================== IMPORT PIN ================================
    @staticmethod
    def importPIN(connection,argv):
        if not connection.isOpen():
            connection.open()
        seq = []
        success = False
        connection.write(AT.IMSI_check)
        end_time = time.time() + timeout
        while True:
            if time.time() >= end_time: 
                print "Timed Out"
                sys.exit(1)
            else:
                seq.append(connection.readline())
                if AT.OK in seq:
                    break
        IMSI    = seq[1].rstrip('\r\n')
        seq = []
        try:
            with open(Methods.fName) as file:
                for line in file:
                    seq = line.split('-')
                    if seq[0] == IMSI:
                        print "Found valid IMSI. Using provided PIN and PUK codes"
                        PIN = seq[1]
                        PUK = seq[2]
                        success = True
                        break
        except IOError:
            print "Could not read file: " + fName
        if success is not True:
            print "Valid IMSI not found. Using default PIN and PUK codes"
            PIN = PIN_def
            PUK = PUK_def
        print "PIN: " + str(PIN)
        print "PUK: " + str(PUK)          
        
        if success is not True and len(argv)>2:
            answer = raw_input("Are you sure you want to continue? (Y/N)").upper()
            if answer == "Y":
                pass
            else:
                print "Aborting"
                sys.exit(1)       
        connection.close()

#============================== MAIN ==========================================
if __name__ == "__main__":
    main(sys.argv[1:])


# Add CPIN_READY to Import PIN ( Device must be unlocked!!!)
# Fill the PUK block function