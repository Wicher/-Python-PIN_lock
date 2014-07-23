import sys
import serial
import time
import getopt


def main(argv):

    connection = serial.Serial()
    connection.baudrate = 115200

    if argv:
        try:
            opts, args = getopt.getopt(argv, "hp:", ["help", "port="])
        except getopt.GetoptError:
            print "error"
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                help()
                sys.exit()
            elif opt in ("-p", "--port"):
                if "COM" in arg:
                    connection.port = arg
                else:
                    connection.port = "COM" + arg
                lock(connection)
    else:
        print "Input port number or name: ",
        port = raw_input().upper()
        if "COM" in port:
            connection.port = port
        else:
            connection.port = "COM" + port
        lock(connection)

def help():
    print "pomoc"

def lock(connection):
    connection.open()
    print "Connected at " + connection.name + " port"
    connection.write("AT+CFUN=0\r\n")
    time.sleep(3)
    print "Locking phone..."
    connection.write("AT+CFUN=1\r\n")
    time.sleep(3)
    print "Locking successfull..."
    connection.close()

#============================== MAIN ==========================================
if __name__ == "__main__":
    main(sys.argv[1:])