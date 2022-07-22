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
                     retriesOnPolling = False, \
                     autoPrintTransactions = False, \
                     whereToPrint = WhereToPrint.BOTH, \
                     logFile = 'set-pollingaddress.log', \
                     rtsToggle = True)

hart.Start()

exit_event = threading.Event()
def signal_handler(signum, frame):
    hart.Stop()
    exit_event.set()
    sys.exit()

def config_thread(hart):

    #
    # Connect to device
    #
    FoundDevice = None
    pollAddress = 0
    EndPollingAddress = 15

    # This slows down too much which can cause the bus arbitration to fail
    # so only do this while monitoring
    #hart.handlePrintMsg = hartUtil.PrintMsg
    
    print("Searching field device")
    
    while pollAddress <= EndPollingAddress:
        print("polling: " + str(pollAddress))
        CommunicationResult, SentPacket, RecvPacket, FoundDevice = hart.LetKnowDevice(pollAddress)
        if FoundDevice is not None:
            break
        pollAddress += 1


    if (FoundDevice is not None):
        PrintDevice(FoundDevice, hart)
    else:
        print ('Device not found. Leaving Application...')
        hart.Stop()
        exit_event.set()
        sys.exit()

    #
    # For devices with HART maj rev >= 6 get loop current mode using command 7
    #
    loopCurrentMode = -1
    if FoundDevice.hartRev >= 6:
        retStatus, CommunicationResult, SentPacket, RecvPacket = HartCommand(hart, 7, None)
        if retStatus:
            loopCurrentMode = RecvPacket.data[1]
            print("Loop current mode is: " + ("Enabled" if loopCurrentMode == 1 else "Disabled"))
        else:
            print(GetCommErrorString(CommunicationResult) + '\n')
            print("FAILED to read Loop Current Mode. Leaving application...n")
            hart.Stop()
            exit_event.set()
            sys.exit()

    #
    # Choose new polling address
    #
    print('\nCurrent polling address is ' + str(pollAddress))
    try:
        newPollAddress = int(input("Enter new polling address: "))
    except:
        newPollAddress = -1

    if newPollAddress == -1 or newPollAddress > 15:
        print('Invalid polling address. Leaving application...')
        hart.Stop()
        exit_event.set()
        sys.exit()

    #
    # send command 6 to set the new polling address
    #

    if FoundDevice.hartRev <= 5:
        txdata = bytearray(1)
        txdata[0] = newPollAddress
    else:
        txdata = bytearray(2)
        txdata[0] = newPollAddress
        txdata[1] = loopCurrentMode # loop current mode remains the same
        
    retStatus, CommunicationResult, SentPacket, RecvPacket = HartCommand(hart, 6, txdata)
    if retStatus:
        print(GetCommErrorString(CommunicationResult) + '\n')
        print("Polling address is now " + str(newPollAddress))
    else:
        print("FAILED to change polling address\n")

    exit_event.set()
    hart.Stop()


# before starting the communication thread allow hart to detect if the network is in burst mode
print("sync with HART bus")
time.sleep(2)


thread = threading.Thread(target=config_thread, args=(hart,), daemon=False)
thread.start()

# need this to catch Ctrl-C
while not exit_event.is_set():
    time.sleep(0.5)


