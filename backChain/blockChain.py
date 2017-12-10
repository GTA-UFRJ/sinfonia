import shelve
import os
import collections
import time
import bson
import transactions
import config

from Cryptodome.Hash import SHA256
from Cryptodome.Signature import DSS

#Blockchain = dict
## 'last': last block hash
## 'hash': block
## block = {hash:bin({ts:num,transactions:[],last:bin(hash)})}

global CHAIN


def loadChain():
    global CHAIN
    CHAIN = shelve.open(config.CHAIN_PATH + os.sep + 'blocks', writeback=True)


def closeChain():
    global CHAIN
    CHAIN.close()


def createBlock(key, transactions):
    global CHAIN
    try:
        block = collections.OrderedDict()
        block[u'last'] = bson.binary.Binary(CHAIN['last'])
        block[u'ts'] = time.time()
        block[u'trans'] = [(bson.binary.Binary(t[0]),bson.binary.Binary(t[1])) for t in transactions]
        blockData = bson.BSON.encode(block, codec_options=bson.codec_options.CodecOptions(document_class=collections.OrderedDict))
        blockHash = SHA256.new(blockData)
        signer = DSS.new(key, 'fips-186-3')
        blockSignature = signer.sign(blockHash)

        return {blockSignature: blockData}
    except:
        raise Exception('Operation failed.')


def appendBlock(key, block):
    global CHAIN
    try:
        #Check if block is correctly formed
        if not checkBlock(key, block): raise

        #Check if last block placement is correct
        blockData = bson.BSON.decode(block.values()[0], codec_options=bson.codec_options.CodecOptions(document_class=collections.OrderedDict))
        if str(blockData[u'last']) != CHAIN['last']: raise

        #Append block
        CHAIN.update(block)
        CHAIN['last'] = block.keys()[0]
        CHAIN.sync()
    except:
        raise Exception('Invalid block. Nothing was saved.')


def checkBlock(key, block):
    validFields = (u'last', u'ts', u'trans')
    try:
        #Check if exactly one block entry
        if len(block) != 1: raise Exception('Invalid number of entries.')

        #Check Signature
        blockSig = str(block.keys()[0])
        blockHash = SHA256.new(str(block.values()[0]))
        verifier = DSS.new(key, 'fips-186-3')
        verifier.verify(blockHash, blockSig)

        #Check Fields
        blockData = decodeBlockData(block.values()[0])
        if not all(k in blockData for k in validFields): raise Exception('Missing fields.')
        if not all((k in validFields) for k in blockData): raise Exception('Invalid fields.')

        #Check 'ts'
        if not isinstance(blockData[u'ts'], (int, long, float)): raise Exception('Invalid Timestamp.')

        #Check 'last'
        if not isinstance(blockData[u'last'], bson.binary.Binary): raise Exception('Invalid LastBlock format.')
        if not len(blockData[u'last'])==64: raise Exception('Invalid LastBlock length.')

        #Check 'trans'
        if not isinstance(blockData[u'trans'], (tuple,list)): raise Exception('Invalid Transactions.')
        for t in blockData[u'trans']:
            if not transactions.checkTransaction(t): raise Exception('Invalid transaction in block.')

        return True
    except:
        return False


def getBlock(key):
    global CHAIN
    try:
        data = CHAIN[key]
        return data
    except:
        raise Exception('Invalid key.')


def decodeBlockData(blockdata):
    try:
        return bson.BSON.decode(blockdata, codec_options=bson.codec_options.CodecOptions(document_class=collections.OrderedDict))
    except:
        raise Exception('Invalid block.')