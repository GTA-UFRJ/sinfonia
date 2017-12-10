import threading
import rpyc
import config
import time

from Queue import Queue
from transactions import *
from keyManagement import *

PKEY = loadKeypair(config.MANAGEMENT_KEY)
LASTSIG = None
CONN_BC = None
CONN_RPC = None
PENDING = Queue()


def check_pending():
    global LASTSIG
    global CONN_BC
    global PENDING

    while (True):
        time.sleep(config.NODE_TRANSACTION_TIMER)
        try:
            #Reset connection if missing
            if CONN_BC is not None:
                if CONN_BC.closed: CONN_BC = rpyc.connect(config.NODE_IP, config.NODE_PORT)
            else:
                CONN_BC = rpyc.connect(config.NODE_IP, config.NODE_PORT)
                try:
                    LASTSIG = CONN_BC.root.getLastTransaction()[0]
                except:
                    CONN_BC.close()
                    CONN_BC = None
            if CONN_BC == None or CONN_BC.closed: continue

            # Search for pending transactions
            for pending in CONN_BC.root.getTransactionsAfter(LASTSIG):
                PENDING.put(pending)
                LASTSIG = pending[0]

        except Exception as ex:
            print 'MAIN: ' + str(ex)


def handle_pending():
    global PKEY
    global PENDING
    global CONN_BC
    global CONN_RPC

    while (True):
        time.sleep(config.NODE_TRANSACTION_TIMER)
        try:
            t = PENDING.get()
            response = None
            if checkTransaction(t):
                try:
                    tData = decodeTransaction(t)
                    if CONN_BC is None or CONN_BC.closed: raise
                    if CONN_RPC is None or CONN_RPC.closed: CONN_RPC = rpyc.connect(config.RPC_IP, config.RPC_PORT)
                    response = CONN_RPC.root.runCommand(tData['command'])
                except:
                    PENDING.put(t)
                    continue
                rt = createTransaction(PKEY, error=response['error'], result=response['result'], response_to=str(t[0]))
                CONN_BC.root.sendTransaction(rt)

        except Exception as ex:
            print 'PENDING' + str(ex)


def main():
    # Start pending transaction management
    threading.Thread(target=handle_pending).start()

    # Enter main loop
    threading.Thread(target=check_pending).start()

if __name__ == '__main__':
    main()
