import rpyc
import threading
import time
import Queue
import config
import transactions
import blockChain
import bson
import collections
import math
from collections import deque

from rpyc.utils.server import ThreadedServer
from Cryptodome.Hash import SHA256
from Cryptodome.Signature import pss
from keyManagement import loadKeypair, loadPublicKey

LASTINDEXEDBLOCK = ''
T0INDEX = {}
T1INDEX = {}
T0ORDER = deque()
PENDINGTRANSACTIONS = Queue.Queue()
KEY = loadKeypair(config.NODE_KEY_PAIR)
KEY_P = loadPublicKey(config.NODE_PUB_KEY, DER=False)

#Consensus
ROLE = None                     #OR Replica
STATE = 'Norm'                  #Norm,PrePrep,Prep,Commit
VIEW = None
PRE_PREPARE = None
PREPARE = {}
PREPARE_SCORE = {True:0, False:0}
COMMIT = []
COMMIT_SCORE = {True:0, False:0}
PEERS_BASE = [config.NODE_IP, config.PBFT_PORT, config.NODE_PORT]
PEER_COUNT = config.PEER_COUNT
PEER_NUMBER = config.PEER_NUMBER
CONN_DATA = {}

def monitorTransactions():
    #global CONSENSUS_FILE
    global PENDINGTRANSACTIONS
    global KEY
    global KEY_P
    global STATE
    global PEER_COUNT
    global PEERS_BASE
    global PEER_NUMBER
    global PRE_PREPARE
    global PREPARE_SCORE
    global CONN_DATA
    while(True):
        if config.SERVER_VERBOSE: print 'Transaction pooling'
        time.sleep(config.NODE_TRANSACTION_TIMER)
        if STATE != 'Norm': continue
        pendingtransactions = PENDINGTRANSACTIONS
        PENDINGTRANSACTIONS = Queue.Queue()
        candidates = []
        while(True):
            try:
                t = pendingtransactions.get(False)
                candidates.append(t)
            except:
                break
        if len(candidates) > 0:
            # CONSENSUS_FILE.write('STARTED;' + str(time.time()) + '\n')
            if config.SERVER_VERBOSE: print 'Started consensus round'
            block = blockChain.createBlock(KEY, candidates)
            #CONSENSUS OVER CANDIDATES HAPPENS HERE (PEER_NUMBER>1)
            if PEER_COUNT > 1:
                if config.SERVER_VERBOSE: print 'Consensus is PBFT'
                STATE = 'PrePrep'
                if config.SERVER_VERBOSE: print 'Changed state to ' + STATE
                PRE_PREPARE = block
                PREPARE_SCORE[True] += 1
                for n in range(0, PEER_COUNT):
                    if PEER_NUMBER == n: continue
                    if n in CONN_DATA:
                        if CONN_DATA[n]['conn'].closed: CONN_DATA[n]['conn'] = rpyc.connect(PEERS_BASE[0], PEERS_BASE[1] + n)
                    else:
                        CONN_DATA[n] = {'conn': rpyc.connect(PEERS_BASE[0], PEERS_BASE[1] + n)}
                    CONN_DATA[n]['prePrepThread'] = threading.Thread(target=CONN_DATA[n]['conn'].root.prePrepare, args=[block])
                    CONN_DATA[n]['prePrepThread'].start()
                STATE = 'Prep'
                if config.SERVER_VERBOSE: print 'Changed state to ' + STATE

            else:
                #CONSENSUS OVER CANDIDATES HAPPENS HERE (PEER_NUMBER==1)
                if config.SERVER_VERBOSE: print 'Consensus is single.'
                blockChain.appendBlock(KEY_P, block)
                #CONSENSUS_FILE.write('ENDED;' + str(time.time()) + '\n')
                if config.SERVER_VERBOSE: print 'Consensus ended'
                #CONSENSUS_FILE.flush()
                buildIndexes()


def validateTransaction(transaction):
    try:
        global T0INDEX
        global T1INDEX

        #Check transaction validity
        if not transactions.checkTransaction(transaction): raise

        transactionData = transactions.decodeTransaction(transaction)

        if transactionData[u'type'] == 0:
            #Check if duplicated
            if str(transaction[0]) in T0INDEX: raise

            #Check if command is acceptable (very basic, probably unsafe for production)
            if any(k in '`><$|;\n' for k in transactionData[u'command']): raise
            if transactionData[u'command'].split()[0] not in ['tacker', 'openstack', 'neutron', 'glance', 'nova', 'heat']: raise

        if transactionData[u'type'] == 1:
            #Check if duplicated
            if str(transaction[0]) in T1INDEX: raise

            #Check if 'response_to' field (type=1) points to existing transaction
            if not str(transactionData[u'response_to']) in T0INDEX: raise

        return True
    except:
        return False

def buildIndexes():
    global T0INDEX
    global T1INDEX
    global T0ORDER
    global LASTINDEXEDBLOCK
    last = blockChain.getBlock('last')
    t0order = deque()
    while(True):
        if str(last) == LASTINDEXEDBLOCK: break
        lastBlock = blockChain.decodeBlockData(blockChain.getBlock(last))
        for k in reversed(range(len(lastBlock[u'trans']))):
            transactionData = transactions.decodeTransaction(lastBlock[u'trans'][k])
            # build index t-sig:{'transaction':(b-sig,num),'response':(b-sig,num)} for type 0 transactions
            # build index t-sig:(b-sig,num)} for type 1 transactions
            if transactionData[u'type'] == 0:
                if not str(lastBlock[u'trans'][k][0]) in T0INDEX: T0INDEX[str(lastBlock[u'trans'][k][0])] = {}
                T0INDEX[str(lastBlock[u'trans'][k][0])]['transaction'] = (str(last), k)
                t0order.appendleft(str(lastBlock[u'trans'][k][0]))
            elif transactionData[u'type'] == 1:
                if not str(transactionData[u'response_to']) in T0INDEX: T0INDEX[str(transactionData[u'response_to'])] = {}
                T0INDEX[str(transactionData[u'response_to'])]['response'] = (str(last), k)
                T1INDEX[str(lastBlock[u'trans'][k][0])] = (str(last), k)
        last = lastBlock[u'last']
    LASTINDEXEDBLOCK = blockChain.getBlock('last')
    T0ORDER.extend(t0order)

class BChainService(rpyc.Service):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def exposed_sendTransaction(self, transaction):
        if not validateTransaction(transaction): return False
        else:
            PENDINGTRANSACTIONS.put(transaction)
            return True

    def exposed_getTransaction(self, sig):
        global T0INDEX
        if sig in T0INDEX:
            if 'transaction' in T0INDEX[sig]:
                blockData = blockChain.decodeBlockData(blockChain.getBlock(T0INDEX[sig]['transaction'][0]))
                return tuple(map(str, blockData[u'trans'][T0INDEX[sig]['transaction'][1]]))
        return None

    def exposed_getTransactionResponse(self, sig):
        global T0INDEX
        if sig in T0INDEX:
            if 'response' in T0INDEX[sig]:
                blockData = blockChain.decodeBlockData(blockChain.getBlock(T0INDEX[sig]['response'][0]))
                return tuple(map(str, blockData[u'trans'][T0INDEX[sig]['response'][1]]))
        return None

    def exposed_getLastTransaction(self):
        global T0ORDER
        sig = T0ORDER[-1]
        return self.exposed_getTransaction(sig)

    def exposed_getTransactionsAfter(self, sig):
        global T0ORDER
        pending = []
        for t in reversed(T0ORDER):
            if t == sig: break
            else: pending.append(self.exposed_getTransaction(t))
        return list(reversed(pending))

class ConsensusService(rpyc.Service):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    @staticmethod
    def encodeMessage(message_dict):
        #message should be ordered dict
        global KEY
        msgData = bson.BSON.encode(message_dict, codec_options=bson.codec_options.CodecOptions(document_class=collections.OrderedDict))
        msgHash = SHA256.new(str(msgData))
        signer = pss.new(KEY)
        msgSignature = signer.sign(msgHash)
        return (msgSignature, msgData)

    @staticmethod
    def checkSignature(message):
        global KEY_P
        try:
            msgSig = str(message[0])
            msgHash = SHA256.new(str(message[1]))
            verifier = pss.new(KEY_P)
            verifier.verify(msgHash, msgSig)
            return True
        except:
            return False

    @staticmethod
    def decodeMessage(message):
        try:
            return bson.BSON.decode(bson.BSON(message[1]), codec_options=bson.codec_options.CodecOptions(document_class=collections.OrderedDict))
        except:
            raise Exception('Invalid message.')

    def exposed_prePrepare(self, message):
        global STATE
        global PEER_COUNT
        global PEERS_BASE
        global PEER_NUMBER
        global CONN_DATA
        global PRE_PREPARE
        global PREPARE
        global PREPARE_SCORE

        #global CONSENSUS_FILE

        #CONSENSUS_FILE.write('STARTED;' + str(time.time()) + '\n')
        if config.SERVER_VERBOSE: print 'Consensus started'

        if config.SERVER_VERBOSE: print 'Entered prePrepare'

        #print 'LEN PREP-P: ' + str(len(message[0])) + '+' + str(len(message[1]))

        accept = True
        if not self.checkSignature(message):
            if config.SERVER_VERBOSE: print 'prePrepare: Signature failed.'
            return False
        if not blockChain.checkBlock(message):
            accept = False
            if config.SERVER_VERBOSE: print 'prePrepare: Block failed.'
        STATE = 'PrePrep'
        if config.SERVER_VERBOSE: print 'Changed state to ' + STATE
        PRE_PREPARE = message
        prep_msg = {'sig': bson.binary.Binary(message[0]), 'from': str(PEER_NUMBER), 'accept': accept}
        signed_prep_msg = self.encodeMessage(prep_msg)
        #print 'LEN P: ' + str(len(signed_prep_msg[0])) + '+' + str(len(signed_prep_msg[1]))
        PREPARE[str(PEER_NUMBER)] = (bson.binary.Binary(signed_prep_msg[0]),bson.binary.Binary(signed_prep_msg[1]))
        PREPARE_SCORE[accept] += 1
        PREPARE_SCORE[True] += 1

        for n in range(0, PEER_COUNT):
            if n==PEER_NUMBER: continue
            if n in CONN_DATA:
                if CONN_DATA[n]['conn'].closed: CONN_DATA[n]['conn'] = rpyc.connect(PEERS_BASE[0], PEERS_BASE[1] + n)
            else:
                CONN_DATA[n] = {'conn': rpyc.connect(PEERS_BASE[0], PEERS_BASE[1] + n)}
            CONN_DATA[n]['prepThread'] = threading.Thread(target=CONN_DATA[n]['conn'].root.prepare, args=[signed_prep_msg])
            CONN_DATA[n]['prepThread'].start()

        STATE = 'Prep'
        if config.SERVER_VERBOSE: print 'Changed state to ' + STATE
        return True

    def exposed_prepare(self, message):
        global PREPARE
        global PREPARE_SCORE

        if not self.checkSignature(message): return False
        decoded_msg = self.decodeMessage(message)
        PREPARE[decoded_msg['from']] = (bson.binary.Binary(message[0]),bson.binary.Binary(message[1]))
        PREPARE_SCORE[decoded_msg['accept']] += 1

        return True

    @staticmethod
    def check_prepare():
        global STATE
        global PEER_COUNT
        global PEERS_BASE
        global PEER_NUMBER
        global CONN_DATA
        global PREPARE
        global PREPARE_SCORE
        global COMMIT
        global COMMIT_SCORE

        target_num = int(math.ceil(PEER_COUNT * (2 / 3.)))
        while (True):
            time.sleep(0.5)
            if STATE != 'Prep': continue

            if PREPARE_SCORE[True] >= target_num or PREPARE_SCORE[False] > target_num:
                commit_msg = {'messages': PREPARE, 'from': str(PEER_NUMBER)}
                signed_commit_msg = ConsensusService.encodeMessage(commit_msg)
                #print 'LEN COMMIT: ' + str(len(signed_commit_msg[0])) + '+' + str(len(signed_commit_msg[1]))
                COMMIT.append(str(PEER_NUMBER))
                COMMIT_SCORE[PREPARE_SCORE[True] > PREPARE_SCORE[False]] += 1

                for n in range(0, PEER_COUNT):
                    if n == PEER_NUMBER: continue
                    if n in CONN_DATA:
                        if CONN_DATA[n]['conn'].closed: CONN_DATA[n]['conn'] = rpyc.connect(PEERS_BASE[0], PEERS_BASE[1] + n)
                    else:
                        CONN_DATA[n] = {'conn': rpyc.connect(PEERS_BASE[0], PEERS_BASE[1] + n)}
                    CONN_DATA[n]['commitThread'] = threading.Thread(target=CONN_DATA[n]['conn'].root.commit, args=[signed_commit_msg])
                    CONN_DATA[n]['commitThread'].start()

                STATE = 'Commit'
                if config.SERVER_VERBOSE: print 'Changed state to ' + STATE

    def exposed_commit(self, message):
        global COMMIT
        global COMMIT_SCORE

        if not self.checkSignature(message): return False

        decoded_msg = self.decodeMessage(message)
        if decoded_msg['from'] in COMMIT: return False
        score = {True:1, False:0}
        for prep_msg in decoded_msg['messages'].values():
            if not self.checkSignature(prep_msg):
                score[False] += 1
                continue
            decoded_prep_msg = self.decodeMessage(prep_msg)
            score[decoded_prep_msg['accept']] += 1
        COMMIT_SCORE[score[True] > score[False]] += 1
        COMMIT.append(decoded_msg['from'])

        return True

    @staticmethod
    def check_commit():
        global STATE
        global PEER_COUNT
        global COMMIT
        global COMMIT_SCORE
        global PREPARE
        global PREPARE_SCORE
        global PRE_PREPARE
        global ROLE

        #global CONSENSUS_FILE

        target_num = int(math.ceil(PEER_COUNT * (2 / 3.)))
        while (True):
            time.sleep(0.5)
            if STATE != 'Commit': continue
            if config.SERVER_VERBOSE: print 'Commit score: ' + str(COMMIT_SCORE)
            if (COMMIT_SCORE[True] >= target_num) or (COMMIT_SCORE[False] > target_num):
                if blockChain.getBlock('last') != PRE_PREPARE[0]:
                    blockChain.appendBlock(KEY_P, PRE_PREPARE)
                    #CONSENSUS_FILE.write('ENDED;' + str(time.time()) + '\n')
                    #CONSENSUS_FILE.flush()
                    buildIndexes()
                    PRE_PREPARE = None
                    PREPARE = {}
                    PREPARE_SCORE = {True: 0, False: 0}
                    COMMIT = []
                    COMMIT_SCORE = {True: 0, False: 0}
                    STATE = 'Norm'
                    if config.SERVER_VERBOSE: print 'Changed state to ' + STATE
                    if config.SERVER_VERBOSE: print 'Concluded PBFT consensus round'

    def exposed_viewChange(self, message):
        pass

    def exposed_getLastBlockSig(self):
        return blockChain.getBlock('last')

    def exposed_getBlocksAfter(self, sig):
        blockChain.getBlock(sig)
        blocks = []
        last = blockChain.getBlock('last')
        while(True):
            if last == sig: break
            block = blockChain.getBlock(last)
            blocks.append({last: block})
            last = str(blockChain.decodeBlockData(block)[u'last'])
        return reversed(blocks)

def main():
    global ROLE
    global PEER_NUMBER
    if PEER_NUMBER == 0:
        ROLE = 'Primary'
    else:
        ROLE = 'Replica'
    blockChain.loadChain()                                             #Load chain
    buildIndexes()                                                     #Create memory indexes
    if ROLE == 'Primary':
        threading.Thread(target=monitorTransactions).start()  # Start transaction monitor
        if config.SERVER_VERBOSE: print 'Started consensus thread.'
    server = ThreadedServer(BChainService, port=config.SERVER_PORT + PEER_NUMBER)  # Create listen service
    threading.Thread(target=server.start).start()  # Start listen service
    if config.SERVER_VERBOSE: print 'Started BC Service on port ' + str(config.SERVER_PORT + PEER_NUMBER)
    cserver = ThreadedServer(ConsensusService, port=config.PBFT_PORT + PEER_NUMBER)  # Create consensus listen service
    threading.Thread(target=cserver.start).start()  # Start consensus listen service
    if config.SERVER_VERBOSE: print 'Started PBFT Service on port ' + str(config.SERVER_PORT + PEER_NUMBER)
    threading.Thread(target=ConsensusService.check_prepare).start()
    threading.Thread(target=ConsensusService.check_commit).start()


###Testing utils
#CONSENSUS_FILE = open('consensus_measurements.txt', 'w')
TRANSACTION_COUNTER = 0
FILE_N = 1
def transaction_counter():
    global FILE_N
    global TRANSACTION_COUNTER
    global PENDINGTRANSACTIONS
    f = open('transaction_measurements_3_'+str(config.PEER_COUNT)+'_'+str(FILE_N)+'.txt', 'w')
    last_n = FILE_N
    while True:
        time.sleep(1)
        f.write(str(TRANSACTION_COUNTER)+' '+str(time.time()).replace('.', ',')+' '+str(PENDINGTRANSACTIONS.qsize())+'\n')
        f.flush()
        if last_n <> FILE_N:
            f.close()
            f = open('transaction_measurements_3_' + str(config.PEER_COUNT) + '_' + str(FILE_N) + '.txt', 'w')
            last_n = FILE_N
###End testing utils


if __name__ == '__main__':
    main()
