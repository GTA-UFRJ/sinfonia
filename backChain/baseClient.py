import rpyc

CONN = None


def connect(host, port=5755):
    global CONN
    if CONN is not None: CONN.close()
    CONN = rpyc.connect(host, port)


def sendTransaction(transaction):
    global CONN
    if (CONN is not None) and (not CONN.closed):
        return CONN.root.sendTransaction(transaction)

def getTransaction(sig):
    global CONN
    if (CONN is not None) and (not CONN.closed):
        return CONN.root.getTransaction(sig)


def getTransactionResponse(sig):
    global CONN
    if (CONN is not None) and (not CONN.closed):
        return CONN.root.getTransactionResponse(sig)


def getLastTransaction():
    global CONN
    if (CONN is not None) and (not CONN.closed):
        return CONN.root.getLastTransaction()


def getTransactionsAfter(sig):
    global CONN
    if (CONN is not None) and (not CONN.closed):
        return CONN.root.getTransactionsAfter(sig)