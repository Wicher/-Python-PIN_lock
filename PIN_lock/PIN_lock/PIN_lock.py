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
    import serial
    from os     import system 
    from getopt import getopt
    from random import randint
    from sys    import exit, argv
    from time   import sleep, time
except ImportError, error:
    print "Error while loading modules: " + str(error)

#Time constants
timeout     = 2
time_sleep  = 1

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

class label:
    no_com_port_specified   = "No com port specified"
    lock_failed             = "Lock failed - actual state: "
    unlock_failed           = "Unlock failed - actual state: "
    device_is_unlocked      = "Device is unlocked"
    device_is_PIN_locked    = "Device is PIN locked"
    device_is_PUK_locked    = "Device is PUK locked"
    device_is_PIN2_locked   = "Device is PIN2 locked"
    device_is_PUK2_locked   = "Device is PUK2 locked"   
    device_is_SIM_locked    = "SIM lock is required"
    device_is_PH_NT_locked  = "Network personalisation is required"
       

def main(argv):

    connection = serial.Serial()
    connection.baudrate = 115200
    connection.timeout = 3

    if argv:
        try:
            opts, args = getopt(argv, "hmc:lbprs", ["help", "modem", "comport=", "lock", "block", "pin", "reset", "state"])
        except getopt.GetoptError:
            print "Invalid argument(s)"
            exit(1)
        for opt, arg in opts[:1]:
            if opt in ("-h", "--help"):
                Options.help()
                exit(1)
            elif opt in ("-m", "--modem"):
                Options.activate_modem()
                exit(1)
            elif opt in ("-c", "--comport"):
                Methods.import_PIN()
                Options.connect(connection,arg)
                break
            else:
                print label.no_com_port_specified
                assert False, label.no_com_port_specified

        for opt, arg in opts[1:]:
            if opt in ("-l", "--lock"):
                Commands.pin_lock(connection)   
            elif opt in ("-b", "--block"):
                Commands.puk_block(connection)          
            elif opt in ("-p", "--pin"):
                Commands.pin_enter(connection)    
            elif opt in ("-r", "--reset"):
                Commands.pin_reset(connection)
            elif opt in ("-s", "--state"):
                Commands.pin_state(connection, True, True) 
            else:
                print label.no_com_port_specified
                assert False, label.no_com_port_specified
    else:
        Options.help()
        exit(1)

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
        system(Options.modem_activate)

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
            exit(1)
        if connection.isOpen():
            print "Connected at " + connection.name.upper() + " port" 
        else: 
            print "Port " + connection.name.upper() + " is not opened" 
            exit(1)

###############################################################################
#                               COMMANDS                                      #
###############################################################################
class Commands:
    #============================== PIN LOCK ================================== OK
    @staticmethod
    def pin_lock(connection):    
        if AT.CPIN_ready == Commands.pin_state(connection):
            connection.write(AT.SIM_disable)
            sleep(time_sleep)
            print "Locking phone..."
            connection.write(AT.SIM_enable)
            sleep(time_sleep)
            if AT.lock_PIN == Commands.pin_state(connection):
                print label.device_is_PIN_locked
            else:
                print label.lock_failed,; Commands.pin_state(connection, True, True)
                print "Check if SIM card's PIN lock is enabled" 
        elif Commands.pin_state(connection, True, True):
            pass

    #============================== PUK BLOCK ================================= TO DO
    @staticmethod
    def puk_block(connection):
        if AT.CPIN_ready == Commands.pin_state(connection):
            Commands.pin_lock(connection)
        if AT.lock_PIN == Commands.pin_state(connection):
            for counter in range(3):
                connection.write(AT.PIN_enter(Methods.random_PIN(True)))
                sleep(time_sleep)
            if AT.lock_PUK == Commands.pin_state(connection):
                print label.device_is_PUK_locked
            else:
                print label.lock_failed,; Commands.pin_state(connection, True, True)
        elif Commands.pin_state(connection,True,True):
            pass

    #============================== PIN ENTER ================================= OK
    @staticmethod
    def pin_enter(connection):
        if AT.lock_PIN == Commands.pin_state(connection):
            connection.write(AT.PIN_enter(PIN))
            sleep(time_sleep)
            if AT.CPIN_ready == Commands.pin_state(connection):
                print label.device_is_unlocked
            else:
                print label.unlock_failed,; Commands.pin_state(connection, True, True)
        elif Commands.pin_state(connection,True,True):
            pass

    #============================== PIN RESET ================================= OK
    @staticmethod
    def pin_reset(connection):
        if AT.lock_PUK == Commands.pin_state(connection):
            connection.write(AT.PUK_enter(PIN, PUK))
            sleep(time_sleep)
            if AT.CPIN_ready == Commands.pin_state(connection):
                print label.device_is_unlocked
            else:
                print label.unlock_failed,; Commands.pin_state(connection, True, True)
        elif Commands.pin_state(connection,True,True):
            pass

    #============================== PIN STATE ================================= OK
    @staticmethod
    def pin_state(connection, printable=False, disconnect=False):
        if not connection.isOpen():
            connection.open()
        seq = []
        connection.write(AT.CPIN_check)
        end_time = time() + timeout
        while True:
            if time() >= end_time:
                print "Timed Out"
                exit(1)
            else:
                seq.append(connection.readline())
                if AT.CPIN_ready in seq:
                    if printable == True:
                        print label.device_is_unlocked
                    result = AT.CPIN_ready
                    break
                elif AT.lock_PIN in seq:
                    if printable == True:
                        print label.device_is_PIN_locked
                    result = AT.lock_PIN
                    break
                elif AT.lock_PUK in seq:
                    if printable == True:
                        print label.device_is_PUK_locked
                    result = AT.lock_PUK
                    break
                elif AT.lock_PIN2 in seq:
                    if printable == True:
                        print label.device_is_PIN2_locked
                    result = AT.lock_PIN2
                    break
                elif AT.lock_PUK2 in seq:
                    if printable == True:
                        print label.device_is_PUK2_locked
                    result = AT.lock_PUK2
                    break
                elif AT.lock_PH_SIM in seq:
                    if printable == True:
                        print label.device_is_SIM_locked
                    result = AT.lock_PH_SIM
                    break
                elif AT.lock_PH_NT in seq:
                    if printable == True:
                        print label.device_is_PH_NT_locked 
                    result = AT.lock_PH_NT
                    break 
        if disconnect == True:
            connection.close()
        return result 

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
                        continue
                    if seq[0] == "PUK":
                        PUK = str(seq[2].rstrip('\r\n'))
                        continue
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
            exit(1)

    #============================== RANDOM PIN ================================ OK
    @staticmethod
    def random_PIN(printable = False):
        wrong_PIN = ''
        for counter in range(4):
            wrong_PIN += str(randint(0,9))
        if wrong_PIN == PIN:
            wrong_PIN = random_PIN()
        if printable == True:
            print wrong_PIN
        return wrong_PIN

#============================== MAIN ========================================== OK
if __name__ == "__main__":
    main(argv[1:])