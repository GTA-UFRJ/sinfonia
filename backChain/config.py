import os

#Server Configuration
NODE_PORT = 5755
NODE_TRANSACTION_TIMER = 1.0
NODE_KEY_PAIR = 'chainNodePrivate'
NODE_PUB_KEY = 'chainNodePublic'
CHAIN_PATH = 'backChain' + os.sep + 'chain'
PEER_COUNT = 1
PEER_NUMBER = 0
SERVER_VERBOSE = True
PBFT_PORT = 12800

#Management Configuration
MANAGEMENT_KEY = 'managementPrivate'

#Interface Configuration
CLIENT_KEY_PAIR = 'sinfonia_private'

#Client Configuration
NODE_IP = 'localhost'

#Key Configuration
KEY_PATH = 'backChain' + os.sep + 'keys'

#PRC
RPC_IP = '10.240.114.132'
RPC_PORT = 2346