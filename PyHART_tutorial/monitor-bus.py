import sys
sys.path.append('../')
from PyHART.COMMUNICATION.CommCore import *
from PyHART.COMMUNICATION.Types import *
from PyHART.COMMUNICATION.Utils import *
from PyHART.COMMUNICATION.Device import *
from PyHART.COMMUNICATION.Packet import *
from PyHART.COMMUNICATION.Common import *

import signal
import threading

class PrintUtil:

    def __init__(self):
        self.prevTime = None

    def getAddressString(self, packet):
        return "".join('{0:02X}'.format(val) for i, val in enumerate(packet.address[0:HartPacket.ADDR_SIZE]))

    def PrintMsg(self, evtType, evtArgs):
        if (evtType == Events.OnCommDone):
            if ((evtArgs.CommunicationResult == CommResult.Ok) or (evtArgs.CommunicationResult == CommResult.ChecksumError)):

                # start time of the packet
                mst = evtArgs.rxPacket.startTime.strftime('%H:%M:%S.%f')
                print("{0} ".format(mst), end='')

                # gap between this packet and the previous packet
                if self.prevTime is not None:
                    ms = (evtArgs.rxPacket.startTime - self.prevTime).microseconds / 1000
                    print("{:3} ".format(int(ms)), end='')
                self.prevTime = evtArgs.currtime

                if (evtArgs.packetType == PacketType.ACK):
                        print("[ACK]   ", end='')

                elif (evtArgs.packetType == PacketType.OACK):
                        print("[OACK]  ", end='')

                elif (evtArgs.packetType == PacketType.BACK):
                        print("[BACK]  ", end='')

                elif (evtArgs.packetType == PacketType.OBACK):
                        print("[OBACK] ", end='')

                elif (evtArgs.packetType == PacketType.STX):
                        print("[STX]   ", end='')

                elif (evtArgs.packetType == PacketType.OSTX):
                        print("[OSTX]  ", end='')

                else:
                        print("[UNKNOWN] ", end='')

                print(self.getAddressString(evtArgs.rxPacket), end='')
                print(" Cmd: {0:d}".format(evtArgs.rxPacket.command), end='')
                print(", rc: 0x{0:02X}, ds: 0x{1:02X}, data: {2:d}".format(evtArgs.rxPacket.resCode, evtArgs.rxPacket.devStatus, evtArgs.rxPacket.dataLen), end='')

                print(''.join('{:02X}'.format(x) for x in evtArgs.rxPacket.data[0:evtArgs.rxPacket.dataLen]), end='')

                print()

                if (evtArgs.CommunicationResult == CommResult.ChecksumError):
                        print ("- CHECKSUM ERROR -")

            elif (evtArgs.CommunicationResult == CommResult.FrameError):
                    print("[FRAME ERROR]")



#
# Procedure to list communication ports
#
count, listOfComPorts = ListCOMPort(True)
comport = None
selection = 0
while (comport == None) and (selection != (count + 1)):
    print ('\nSelect the communication port.')
    print('Insert the number related to your choice and press enter.')
    try:
        selection = int(input())
    except:
        selection = 0

    if (selection == (count + 1)):
        print('Leaving application...')
        sys.exit()

    comport = GetCOMPort(selection, listOfComPorts)


#
# Instantiates and starts the communication object
#
hart = HartMasterOnW(comport, \
                     MASTER_TYPE.SECONDARY, \
                     num_retry = 10, \
                     retriesOnPolling = False, \
                     autoPrintTransactions = False, \
                     whereToPrint = WhereToPrint.BOTH, \
                     logFile = 'monitor-bus.log', \
                     rtsToggle = True)

hart.Start()

exit_event = threading.Event()

def signal_handler(signum, frame):
    exit_event.set()
    sys.exit()

signal.signal(signal.SIGINT, signal_handler)

printUtil = PrintUtil()
hart.handlePrintMsg = printUtil.PrintMsg

def monitor_thread(hart):
    while not exit_event.is_set():
        time.sleep(0.1)
    hart.Stop()

thread = threading.Thread(target=monitor_thread, args=(hart,), daemon=True)
thread.start()

# need this to catch Ctrl-C
while not exit_event.is_set():
    time.sleep(0.5)
