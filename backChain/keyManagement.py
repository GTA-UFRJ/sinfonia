import os
import string
import config

from Cryptodome.PublicKey import ECC


def generateKeypair(keyname):
    try:
        fname = keyname.translate(string.maketrans('',''),'<>:"/\\|?*')
        key = ECC.generate(curve='P-256')
        with open(config.KEY_PATH+os.sep+fname+'.pem','w') as f:
            f.write(key.export_key(format='PEM'))
            print 'Private key generated: ' + fname
        return key
    except:
        raise Exception('Error trying to generate key with given identifier.')


def loadKeypair(keyname):
    try:
        fname = keyname.translate(string.maketrans('', ''), '<>:"/\\|?*')
        with open(config.KEY_PATH + os.sep + fname + '.pem') as f:
            key = ECC.import_key(f.read())
            if not key.has_private(): raise
            else: return key
    except:
        raise Exception('No private key found with given identifier.')


def exportPublicKey(key,keyname):
    try:
        fname = keyname.translate(string.maketrans('',''),'<>:"/\\|?*')
        with open(config.KEY_PATH+os.sep+fname+'.pem','w') as f:
            f.write(key.public_key().export_key(format='PEM'))
            print 'Public key exported: ' + fname
    except:
        raise Exception('Error trying to generate key with given identifier.')


def loadPublicKey(keyname, DER=True):
    try:
        fname = keyname.translate(string.maketrans('', ''), '<>:"/\\|?*')
        with open(config.KEY_PATH + os.sep + fname + '.pem') as f:
            key = ECC.import_key(f.read())
            if DER: return key.public_key().export_key(format='DER')
            else: return key.public_key()
    except:
        raise Exception('No public key found with given identifier.')


def listKeys():
    private = ['Private keys:']
    public = ['Public keys:']
    for (dirpath, dirnames, filenames) in os.walk(config.KEY_PATH):
        for filename in filenames:
            try:
                with open(dirpath+os.sep+filename) as f:
                    key = ECC.import_key(f.read())
                    if key.has_private(): private.append('\t'+os.path.splitext(filename)[0])
                    else: public.append(os.path.splitext('\t'+filename)[0])
            except:
                pass
    for privkey in private: print privkey
    for pubkey in public: print pubkey