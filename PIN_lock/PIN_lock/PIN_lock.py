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
import serial
import time
import getopt

PIN_code = 1111
PUK_code = 11111111


def main(argv):

    connection = serial.Serial()
    connection.baudrate = 115200
    connection.timeout = 3

    if argv:
        try:
            opts, args = getopt.getopt(argv, "hc:lpr", ["help", "comport=", "lock", "pin", "reset"])
        except getopt.GetoptError:
            print "Invalid argument(s)"
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                help()
                sys.exit()
            elif opt in ("-c", "--comport"):
                connect(connection,arg)
                break
            else:
                print "No com port specified"
                assert False, "No com port specified"

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                help()
                sys.exit()
            elif opt in ("-l", "--lock"):
                pin_lock(connection)   
            elif opt in ("-p", "--pin"):
                pin_enter(connection)      
                 

    else:
        print "Input port number or name: ",
        port = raw_input().upper()
        pin_lock(connection,port)

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


#============================== LOCK ==========================================
def pin_lock(connection):
    connection.write("AT+CFUN=0\r\n")
    time.sleep(2)
    print "Locking phone..."
    connection.write("AT+CFUN=1\r\n")
    time.sleep(2)
    print "Locking successful" 
    connection.close()

#============================== PIN ENTER =====================================
def pin_enter(connection):
    seq = []
    connection.write("AT+CPIN=" + str(PIN_code) + "\r\n")
    seq.append(connection.readline())
    seq.append(connection.readline())
    connection.write("AT+CPIN?\r\n")
    seq.append(connection.readline())
    seq.append(connection.readline())
    if seq[3] == "+CPIN: READY\r\n":
        print "Unlocking successful"

    connection.close()   

#============================== HELP ==========================================
def help():
    print "========== HELP =========="
    print "syntax: \n \t PIN_lock.py [option] ([parameter]) \n"
    print "Options:"
    print "  -h --help     Show this help message and exit"
    print "  -c --comport  Connect to specified COM port"
    print "  -l --lock     PIN lock device"
    print "  -p --pin      Enter default PIN code"
    print "  -r --reset    Reset the PUK locked device with default PIN code"





#============================== MAIN ==========================================
if __name__ == "__main__":
    main(sys.argv[1:])