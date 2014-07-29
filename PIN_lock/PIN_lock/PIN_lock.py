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
try:
    import sys
    import os 
    import serial
    import time
    import getopt
    import random
except ImportError, error:
    print "Error while loading modules: " + str(error)

timeout = 2

#PIN and PUK codes
PIN         = ''
PUK         = ''
PIN_def     = '1111'
PUK_def     = '11111111'

class AT:
    #COMMANDS
    CPIN_check  = 'AT+CPIN?\r\n'
    SIM_enable  = 'AT+CFUN=1\r\n'
    SIM_disable = 'AT+CFUN=0\r\n'
    
    #RESPONSES
    OK          = 'OK\r\n'
    CPIN_ready  = '+CPIN: READY\r\n'
    lock_PIN    = '+CPIN: SIM PIN\r\n'
    lock_PUK    = '+CPIN: SIM PUK\r\n'
    lock_PIN2   = '+CPIN: SIM PIN2\r\n'
    lock_PUK2   = '+CPIN: SIM PUK2\r\n'
    lock_PH_SIM = '+CPIN: PH-SIM PIN\r\n'
    lock_PH_NT  = '+CPIN: PH-NET PIN\r\n'
    
    @staticmethod
    def PIN_enter(PIN):
        return "AT+CPIN=" + PIN + "\r\n"

    @staticmethod
    def PUK_enter(PIN,PUK):
        return "AT+CPIN=" + PUK + "," + PIN + "\r\n"


def main(argv):

    connection = serial.Serial()
    connection.baudrate = 115200
    connection.timeout = 3

    if argv:
        try:
            opts, args = getopt.getopt(argv, "hmc:lbpsr", ["help", "modem", "comport=", "lock", "block", "pin", "state",  "reset"])
        except getopt.GetoptError:
            print "Invalid argument(s)"
            sys.exit(1)
        for opt, arg in opts[:1]:
            if opt in ("-h", "--help"):
                Options.help()
                sys.exit(1)
            elif opt in ("-m", "--modem"):
                Options.activate_modem()
                sys.exit(1)
            elif opt in ("-c", "--comport"):
                Methods.import_PIN()
                Options.connect(connection,arg)
                break
            else:
                print "No com port specified"
                assert False, "No com port specified"

        for opt, arg in opts[1:]:
            if opt in ("-l", "--lock"):
                Commands.pin_lock(connection)   
            elif opt in ("-b", "--block"):
                #Commands.puk_block(connection)  
                pass              
            elif opt in ("-p", "--pin"):
                Commands.pin_enter(connection)    
            elif opt in ("-s", "--state"):
                Commands.pin_state(connection, True, True) 
            elif opt in ("-r", "--reset"):
                Commands.pin_reset(connection)
            else:
                print "No com port specified"
                assert False, "No com port specified"    
    else:
        Options.help()
        sys.exit(1)

###############################################################################
#                               OPTIONS                                       #
###############################################################################
class Options:
    modem_activate = "adb root && timeout 2 && adb remount && adb shell setprop persist.usb.eng 1 && adb shell setprop sys.usb.config mtp,adb && timeout 3"
    #============================== HELP ====================================== OK
    @staticmethod
    def help():
        print "==================== HELP ===================="
        print "syntax: \n \t PIN_lock.py [option] ([command]...) \n \t"
        print "Support for parameter chaining (direction from left to right) \n"
        print "Please remember to update PIN.txt with SIM card's PIN and PUK codes \n"
        print "Option:"
        print "  -h --help      Show this help message and exit"
        print "  -m --modem     Activate modem and exit"
        print "  -c --comport   Connect to specified COM port"
        print "Command:"
        print "  -l --lock      PIN lock device"
        print "  -b --block     PUK block device"
        print "  -p --pin       Enter default PIN code"
        print "  -s --state     Get SIM lock state"
        print "  -r --reset     Reset the PUK locked device with default PIN code"

    #============================== MODEM ===================================== OK
    @staticmethod
    def activate_modem():
        os.system(Options.modem_activate)

    #============================== CONNECTION ================================ OK
    @staticmethod
    def connect(connection,port):
        if "COM" in port.upper():
            connection.port = port
        else:
            connection.port = "COM" + port
        try:
            connection.open()
        except Exception, error:
            print "Error while opening serial port: " + str(error)
            sys.exit(1)
        if connection.isOpen():
            print "Connected at " + connection.name.upper() + " port" 
        else: 
            print "Port " + connection.name.upper() + " is not opened" 
            sys.exit(1)

###############################################################################
#                               COMMANDS                                      #
###############################################################################
class Commands:
    #============================== PIN LOCK ================================== OK
    @staticmethod
    def pin_lock(connection):    
        if AT.CPIN_ready == Commands.pin_state(connection):
            connection.write(AT.SIM_disable)
            time.sleep(1)
            print "Locking phone..."
            connection.write(AT.SIM_enable)
            time.sleep(1)
            if AT.lock_PIN == Commands.pin_state(connection):
                print "Device is locked"
            else:
                print "Lock failed - actual state: " + Commands.pin_state(connection)
        elif Commands.pin_state(connection,True,True):
            pass

    #============================== PUK BLOCK ================================= TO DO
    @staticmethod
    def puk_block(connection):
        if not connection.isOpen():
            connection.open()
        seq = []
        leave = False
        connection.write(AT.CPIN_check)
        while True:
            seq.append(connection.readline())
            if AT.lock_PIN in seq:
                for counter in range(3):
                    wrong_PIN = Methods.random_PIN()
                    #connection.write(AT.PIN_enter(wrong_PIN))
                    print wrong_PIN
                    time.sleep(1)
                break
        Commands.pin_state(connection)
               
        connection.close() 

    #============================== PIN ENTER ================================= OK
    @staticmethod
    def pin_enter(connection):
        if AT.lock_PIN == Commands.pin_state(connection):
            connection.write(AT.PIN_enter(PIN))
            time.sleep(1)
            if AT.CPIN_ready == Commands.pin_state(connection):
                print "Device is unlocked"
            else:
                print "Unlock failed - actual state: " + Commands.pin_state(connection)
        elif Commands.pin_state(connection,True,True):
            pass

    #============================== PIN STATE ================================= OK
    @staticmethod
    def pin_state(connection, printable=False, disconnect=False):
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
                    if printable == True:
                        print "Device is unlocked"
                    result = AT.CPIN_ready
                    break
                elif AT.lock_PIN in seq:
                    if printable == True:
                        print "Device is PIN locked"
                    result = AT.lock_PIN
                    break
                elif AT.lock_PUK in seq:
                    if printable == True:
                        print "Device is PUK locked"
                    result = AT.lock_PUK
                    break
                elif AT.lock_PIN2 in seq:
                    if printable == True:
                        print "Device is PIN2 locked"
                    result = AT.lock_PIN2
                    break
                elif AT.lock_PUK2 in seq:
                    if printable == True:
                        print "Device is PUK2 locked"
                    result = AT.lock_PUK2
                    break
                elif AT.lock_PH_SIM in seq:
                    if printable == True:
                        print "SIM lock is required"
                    result = AT.lock_PH_SIM
                    break
                elif AT.lock_PH_NT in seq:
                    if printable == True:
                        print  "Network personalisation is required"
                    result = AT.lock_PH_NT
                    break 
        if disconnect == True:
            connection.close()
        return result 

    #============================== PIN RESET ================================= TO DO
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
                connection.write(AT.PUK_enter(PIN,PUK))
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
    #============================== IMPORT PIN ================================ OK
    @staticmethod
    def import_PIN():
        global PIN
        global PUK
        try:
            with open(Methods.fName) as file:
                for line in file :
                    seq = line.split(' ')               
                    if seq[0] == "PIN":
                        PIN = str(seq[2].rstrip('\r\n'))
                    if seq[0] == "PUK":
                        PUK = str(seq[2].rstrip('\r\n'))
        except IOError: 
            print "Could not read file: " + fName
            print "Using default codes"
            PIN = PIN_def
            PUK = PUK_def   
        print "PIN: " + PIN
        print "PUK: " + PUK
        answer = raw_input("Proceed? (Y/N): ").upper()
        if answer == 'Y' or answer == '':
            pass
        else:
            sys.exit(1)

    #============================== RANDOM PIN ================================ OK
    @staticmethod
    def random_PIN():
        wrong_PIN = ''
        for counter in range(4):
            wrong_PIN += str(random.randint(0,9))
        if wrong_PIN == PIN:
            wrong_PIN = random_PIN()
        return wrong_PIN

#============================== MAIN ========================================== OK
if __name__ == "__main__":
    main(sys.argv[1:])

# Modify the PUK_block and PIN_reset function
# Add labels