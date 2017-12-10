# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time
import demjson
import rpyc
import backChain.keyManagement as keyManagement
import backChain.transactions as transactions
import backChain.config as config


BLOCKCHAIN = True
CREATE_RESPONSE = True
RPC_IP = '10.240.114.132'
RPC_PORT = 2346
CONN = None


def decode_tabular_output(t, none_value=None):
    if len(t) == 0: return none_value
    if t[-1] != '\n': t += '\n'
    lines = unicode(t).split('\n')
    first = 0
    message = ''
    table = False
    decode_entry = lambda x, y: (x, demjson.decode(y.replace("u'", "'"))) if (len(y) > 0 and y[0] == '{') else (x, y)
    ret = {}

    try:
        # Get first tabular line or resolve single dictionary
        for line in lines:
            if len(line) == 0:
                first += 1
            elif line[0] == '+':
                table = True
                break
            elif line[0] == '{':
                ret = demjson.decode(''.join(lines[first:]))
                break
            else:
                message += line
                first += 1
        if table:
            # Get headers
            headers = [k.strip() for k in lines[first + 1].split('|')[1:-1]]

            # For Field/Value yield dictionary {field:value}
            if headers[0] == 'Field' and headers[1] == 'Value':
                ret = {u'message': message[:-1]}
                last_field = None
                for line in lines[first + 3:-2]:
                    entry = tuple(k.strip() for k in line.split('|')[1:-1])
                    if entry[0] != '':
                        last_field = entry[0]
                        ret.update([decode_entry(*entry)])
                    else:
                        if not isinstance(ret[last_field], list): ret[last_field] = [ret[last_field]]
                        ret[last_field].append(entry[1])

            # For other cases yield dictionary list[{column-0:value-0},...,{column-n:value-n}]
            else:
                ret = []
                for line in lines[first + 3:-2]:
                    ret.append(dict(map(decode_entry, headers, [k.strip() for k in line.split('|')[1:-1]])))
        else:
            if len(message) > 0:
                if message[-1] == '\n': message = message[:-1]
            ret[u'message'] = message

        return ret
    except:
        raise


def runCreateOrDeleteCommand(command, user):
    global BLOCKCHAIN
    global CREATE_RESPONSE
    r = None
    try:
        if not BLOCKCHAIN:
            r = runCommand(command, {})
        else:
            key = keyManagement.loadKeypair(config.CLIENT_KEY_PAIR)
            t = transactions.createTransaction(key, user=user, command=command)
            conn = rpyc.connect(config.NODE_IP, config.NODE_PORT)
            if not conn.root.sendTransaction(t): raise
            r = {'result': {'message': 'Command sent.'}, 'error': 'WARNING: Result not requested.'}
            rt = None
            if CREATE_RESPONSE:
                max_retries = 20
                while rt is None and max_retries > 0:
                    time.sleep(1.0)
                    rt = conn.root.getTransactionResponse(t[0])
                    max_retries -= 1
                if rt is None: raise Exception('No response transaction data.')
                rt_data = transactions.decodeTransaction(rt)
                r = {'result': rt_data['result'], 'error': rt_data['error']}
                r['result'] = decode_tabular_output(r['result'])
            conn.close()
    except:
        r = {'result': {'message': ''}, 'error': 'Server error.'}
    return r


def runCommand(command, result_type=[]):
    global RPC_IP
    global RPC_PORT
    global CONN
    global CREATE_RESPONSE
    try:
        if CONN is None or CONN.closed: CONN = rpyc.connect(RPC_IP, RPC_PORT)
        remote = CONN.root.runCommand(command)
        r = dict()
        r['result'] = decode_tabular_output(remote['result'], result_type)
        r['error'] = remote['error']
        return r
    except:
        return {'result': result_type, 'error': 'RPC server error has ocurred.'}


def create_vnfd(vnfd_dict, user='admin'):
    global RPC_IP
    global RPC_PORT
    global CONN
    global CREATE_RESPONSE
    try:
        if CONN is None or CONN.closed: CONN = rpyc.connect(RPC_IP, RPC_PORT)
        remote = CONN.root.createVNFD(vnfd_dict)
        r = dict()
        r['result'] = decode_tabular_output(remote['result'], [])
        r['error'] = remote['error']
        return r
    except:
        return {'result': [], 'error': 'RPC server error has ocurred.'}


def create_vnf(vnf_name, vnfd_id, user='admin'):
    command = 'tacker vnf-create --name ' + vnf_name + ' --vnfd-id ' + vnfd_id
    return runCreateOrDeleteCommand(command, user)


def create_classifier(classifier_name, chain_id, src_port, dst_port, netproto, user='admin'):
    command = 'tacker sfc-classifier-create --name ' + classifier_name + ' --chain ' + chain_id + ' --match source_port='+ src_port+',dest_port='+dst_port+',protocol='+netproto
    return runCreateOrDeleteCommand(command, user)


def create_sfc(sfc_name, vnf_list, user='admin'):
    command = 'tacker sfc-create --name ' + sfc_name + ' --chain ' + ','.join(vnf_list)
    return runCreateOrDeleteCommand(command, user)


def create_network(net_name, net_cidr, net_dns, net_dhcp_start, net_dhcp_end, user='admin'):
    commands = ['neutron net-create {0}'.format(net_name),
                'neutron subnet-create  --name {0}-subnet  --dns-nameserver {1} --allocation-pool start={2},end={3} --enable-dhcp {0} {4}'.format(net_name, net_dns, net_dhcp_start, net_dhcp_end, net_cidr),
                'neutron router-create {0}-router'.format(net_name),
                'neutron router-gateway-set {0}-router admin_floating_net'.format(net_name),
                'neutron router-interface-add {0}-router {0}-subnet'.format(net_name)]
    r = [runCreateOrDeleteCommand(command, user) for command in commands]
    return {u'network': r[0], u'subnet': r[1], u'router': r[2], u'gateway-set': r[3], u'interface-add': r[4]}


def delete_network(net_name, user='admin'):
    commands = ['neutron router-interface-delete {0}-router {0}-subnet'.format(net_name),
                'neutron router-gateway-clear {0}-router'.format(net_name),
                'neutron router-delete {0}-router'.format(net_name),
                'neutron subnet-delete {0}-subnet'.format(net_name),
                'neutron net-delete {0}'.format(net_name)]
    r = [runCreateOrDeleteCommand(command, user) for command in commands]
    return {u'network': r[4], u'subnet': r[3], u'router': r[2], u'gateway-set': r[1], u'interface-add': r[0]}


def delete_sfc(sfc, user='admin'):
    command = 'tacker sfc-delete ' + sfc
    return runCreateOrDeleteCommand(command, user)


def delete_vnf(vnf, user='admin'):
    command = 'tacker vnf-delete ' + vnf
    return runCreateOrDeleteCommand(command, user)


def delete_vnfd(vnfd, user='admin'):
    command = 'tacker vnfd-delete ' + vnfd
    return runCreateOrDeleteCommand(command, user)


def delete_classifier(classifier, user='admin'):
    command = 'tacker sfc-classifier-delete ' + classifier
    return runCreateOrDeleteCommand(command, user)


def show_sfc(sfc):
    command = 'tacker sfc-show ' + sfc
    return runCommand(command)


def show_vnf(vnf):
    command = 'tacker vnf-show ' + vnf
    return runCommand(command)


def show_classifier(classifier):
    command = 'tacker sfc-classifier-show ' + classifier
    return runCommand(command)


def list_vnfs():
    command = 'tacker vnf-list'
    return runCommand(command)


def list_vnfds():
    command = 'tacker vnfd-list'
    return runCommand(command)


def list_sfcs():
    command = 'tacker sfc-list'
    return runCommand(command)


def list_classifiers():
    command = 'tacker sfc-classifier-list'
    return runCommand(command)


def list_networks():
    command = 'neutron net-list'
    return runCommand(command)


def list_flavors():
    command = 'nova flavor-list'
    return runCommand(command)


def list_images():
    command = 'glance image-list'
    return runCommand(command)


def list_nodes():
    command = 'nova hypervisor-list'
    return runCommand(command)


def list_servers():
    command = 'nova list'
    return runCommand(command)


def get_server_id(resource_id, name='vdu1'):
    command = 'heat resource-list -f name=' + name + ' ' + resource_id
    try:
        return runCommand(command)['result'][0]['physical_resource_id']
    except:
        return ''


def get_host_servers(server_name):
    command = 'nova hypervisor-servers ' + server_name
    return [k['ID'] for k in runCommand(command)['result']]
