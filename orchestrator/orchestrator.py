import rpyc
import threading
import demjson
import time
import random

from subprocess import Popen, PIPE
from rpyc.utils.server import ThreadedServer


PORT = 2346


class OrchestratorService(rpyc.Service):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def exposed_runCommand(self, command):
        r = None
        #Check if command is acceptable (very basic, probably unsafe for production)
        if any(k in '`><$|;\n' for k in command):
            r = {'result': '', 'error': 'Invalid character in command.'}
        elif command.split()[0] not in ['tacker', 'openstack', 'neutron', 'glance', 'nova', 'heat']:
            r = {'result': '', 'error': 'Invalid command.'}
        else:
            #Run command
            p = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = p.communicate()
            r = {'result': stdout, 'error': stderr}
        return r

    def exposed_createVNFD(self, vnfd_json):
        try:
            filename = '/tmp/' + str(time.time()) + str(random.randint(1, 1000000000)) + '.json'
            with open(filename, 'w') as f: f.write(demjson.encode(vnfd_json))
            r = self.exposed_runCommand('tacker vnfd-create -f json --vnfd-file ' + filename)
            return r
        except:
            r = {'result': '', 'error': 'Unexpected error has ocurred.'}
            return r


def main():
    global PORT
    server = ThreadedServer(OrchestratorService, port=PORT)      #Create listen service
    threading.Thread(target=server.start).start()            #Start listen service


if __name__ == '__main__':
    main()
