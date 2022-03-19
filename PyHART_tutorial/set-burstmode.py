import sys
sys.path.append('../')
from PyHART.COMMUNICATION.CommCore import *
from PyHART.COMMUNICATION.Types import *
from PyHART.COMMUNICATION.Utils import *
from PyHART.COMMUNICATION.Device import *
from PyHART.COMMUNICATION.Packet import *
from PyHART.COMMUNICATION.Common import *

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
                     MASTER_TYPE.PRIMARY, \
                     num_retry = 10, \
                     retriesOnPolling = True, \
                     autoPrintTransactions = False, \
                     whereToPrint = WhereToPrint.BOTH, \
                     logFile = 'set-burstmode.log', \
                     rtsToggle = True)

hart.Start()

exit_event = threading.Event()
def signal_handler(signum, frame):
    hart.Stop()
    exit_event.set()
    sys.exit()

def setburstmode_thread(hart):

    #
    # Connect to device at polling address 3
    #
    FoundDevice = None
    pollAddress = 3

    CommunicationResult, SentPacket, RecvPacket, FoundDevice = hart.LetKnowDevice(pollAddress)

    if (FoundDevice is not None):
        PrintDevice(FoundDevice, hart)
        if RecvPacket.address[0] & 0x40:
            print("Device is in Burst Mode.")
        else:
            print("Device is not in Burst Mode.")
    else:
        print ('Device not found. Leaving Application...')
        hart.Stop()
        exit_event.set()
        sys.exit()

    #
    # Choose Burst mode
    #
    print ('\nSelect Burst Mode.')
    print('Insert the number related to your choice and press enter.')
    print('  1: Burst Mode On')
    print('  2: Burst Mode Off')
    print('  3: Quit')
    selection = 0
    try:
        selection = int(input())
    except:
        selection = 0

    if selection == 0 or selection >= 3:
        print('Leaving application...')
        hart.Stop()
        exit_event.set()
        sys.exit()

    #
    # send command 109 to set the burst mode
    #
    txdata = bytearray(1)
    if selection == 1:
        txdata[0] = 1
    else:
        txdata[0] = 0
    retStatus, CommunicationResult, SentPacket, RecvPacket = HartCommand(hart, 109, txdata)
    if retStatus:
        print("Burst Mode is now " + ("on" if selection == 1 else "off"))
        print(GetCommErrorString(CommunicationResult) + '\n')
    else:
        print("FAILED to change burst mode\n")

    exit_event.set()
    hart.Stop()


# before starting the communication thread allow hart to detect if the network is in burst mode
time.sleep(1)


thread = threading.Thread(target=setburstmode_thread, args=(hart,), daemon=False)
thread.start()

# need this to catch Ctrl-C
while not exit_event.is_set():
    time.sleep(0.5)


