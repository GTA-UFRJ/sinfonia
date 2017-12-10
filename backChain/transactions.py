import time
import bson
import collections

from Cryptodome.Hash import SHA256
from Cryptodome.Signature import DSS
from Cryptodome.PublicKey import ECC


def createTransaction(key, **kwargs):
    transaction = collections.OrderedDict()
    transaction_type = None
    if all(k in kwargs for k in ('user', 'command')): transaction_type = 0
    elif all(k in kwargs for k in ('response_to', 'result', 'error')): transaction_type = 1
    else: raise Exception('Invalid transaction fields.')

    transaction[u'ts'] = time.time()
    transaction[u'type'] = transaction_type
    transaction[u'from'] = bson.binary.Binary(key.public_key().export_key(format='DER'))

    if transaction_type == 0:
        transaction[u'user'] = kwargs['user']
        transaction[u'command'] = kwargs['command']

    if transaction_type == 1:
        transaction[u'response_to'] = bson.binary.Binary(str(kwargs['response_to']))
        transaction[u'result'] = kwargs['result']
        transaction[u'error'] = kwargs['error']

    transaction_data = bson.BSON.encode(transaction, codec_options=bson.codec_options.CodecOptions(document_class=collections.OrderedDict))
    transaction_hash = SHA256.new(transaction_data)
    signer = DSS.new(key, 'fips-186-3')
    transaction_signature = signer.sign(transaction_hash)

    return (transaction_signature, transaction_data)


def checkTransaction(transaction):
    validTypes = (0,1)
    type0Fields = ('ts', 'type', 'from', 'command', 'user')
    type1Fields = ('ts', 'type', 'from', 'response_to', 'result', 'error')
    try:
        # Check if exactly one block entry
        if len(transaction) != 2: raise Exception('Invalid number of entries.')

        #Check Signature
        transactionSig = str(transaction[0])
        transactionData = decodeTransaction(transaction)
        key = ECC.import_key(transactionData[u'from'])
        transactionHash = SHA256.new(str(transaction[1]))
        verifier = DSS.new(key, 'fips-186-3')
        verifier.verify(transactionHash, transactionSig)

        #Check Fields
        if ((transactionData[u'type'] == 0) and any(k not in type0Fields for k in transactionData)): raise Exception('Invalid type or fields.')
        if ((transactionData[u'type'] == 0) and (not all(k in transactionData for k in type0Fields))): raise Exception('Missing fields.')
        if ((transactionData[u'type'] == 1) and any(k not in type1Fields for k in transactionData)): raise Exception('Invalid type or fields.')
        if ((transactionData[u'type'] == 1) and (not all(k in transactionData for k in type1Fields))): raise Exception('Missing fields.')

        #Check 'type'
        if not(transactionData[u'type'] in validTypes): raise Exception('Invalid Type.')

        #Check 'ts'
        if not isinstance(transactionData[u'ts'], (int, long, float)): raise Exception('Invalid Timestamp.')

        if transactionData[u'type'] == 0:
            #Check 'command'
            if not isinstance(transactionData[u'command'], (unicode, str)): raise Exception('Invalid Command.')
            if transactionData[u'command'] == '': raise Exception('Invalid Command.')

            #Check 'user'
            if not isinstance(transactionData[u'user'], (unicode, str)): raise Exception('Invalid User.')
            if transactionData[u'user'] == '': raise Exception('Invalid User.')

        if transactionData[u'type'] == 1:
            #Check 'response_to'
            if not isinstance(transactionData[u'response_to'], (bson.binary.Binary, str)): raise Exception('Invalid Response Identifier.')

            #Check 'result'
            if not isinstance(transactionData[u'result'], (unicode, str)): raise Exception('Invalid Result.')

            #Check 'error'
            if not isinstance(transactionData[u'error'], (unicode, str)): raise Exception('Invalid Error.')

        return True
    except:
        return False


def decodeTransaction(transaction):
    try:
        return bson.BSON.decode(bson.BSON(str(transaction[1])), codec_options=bson.codec_options.CodecOptions(document_class=collections.OrderedDict))
    except:
        raise Exception('Invalid transaction.')


def encodeTransaction(key,transaction):
    try:
        transactionData = bson.BSON.encode(transaction, codec_options=bson.codec_options.CodecOptions(document_class=collections.OrderedDict))
        transactionHash = SHA256.new(transactionData)
        signer = DSS.new(key, 'fips-186-3')
        transactionSignature = signer.sign(transactionHash)
        t = (transactionSignature, transactionData)
        if checkTransaction(t): return t
        else: raise Exception('Invalid transaction.')
    except:
        raise Exception('Invalid transaction or key.')