# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.decorators import login_required

from sinfonia_api import *
from forms import *


@login_required
def vnfs_table(request):
    if request.method == 'POST':
        return HttpResponse(request)

    context = dict()
    context['vnfs'] = list_vnfs()['result']

    return HttpResponse(loader.get_template('vnfs_table.html').render(context, request))


@login_required
def vnfds_table(request):
    if request.method == 'POST':
        return HttpResponse(request)

    context = dict()
    context['vnfds'] = list_vnfds()['result']
    context['nodes'] = list_vnfs()['result']


    return HttpResponse(loader.get_template('vnfds_table.html').render(context, request))

@login_required
def networksJSON(request):
    server_dict = {}
    for server in list_servers()['result']:
        server_dict[server['ID']] = server

    host_dict = {}
    for host in list_nodes()['result']:
        host_dict[host['Hypervisor hostname']] = host
        for server in get_host_servers(host['Hypervisor hostname']):
            if server in server_dict: server_dict[server]['host'] = host['Hypervisor hostname']

    net_dict = {}
    for network in list_networks()['result']:
        net_dict[network['name']] = network
        net_dict[network['name']]['subnets'] = net_dict[network['name']]['subnets'].split(' ')[-1]
    if 'admin_floating_net' in net_dict: del net_dict['admin_floating_net']

    vnf_dict = {}
    for vnf in list_vnfs()['result']:
        # Gather data
        vnf_details = show_vnf(vnf['name'])['result']
        server_id = get_server_id(vnf_details['instance_id'])
        networks = (server_dict[server_id]['Networks'].split(', ') if server_id != '' else [])

        # Write dictionary entry
        vnf_dict[vnf['id']] = {}
        vnf_dict[vnf['id']]['name'] = vnf['name']
        vnf_dict[vnf['id']]['network'] = (networks[0].split('=')[0] if len(networks) > 0 else 'None')
        vnf_dict[vnf['id']]['network_ip'] = (networks[0].split('=')[1] if len(networks) > 0 else 'None')
        vnf_dict[vnf['id']]['public_ip'] = (networks[1] if len(networks) > 1 else 'None')
        vnf_dict[vnf['id']]['status'] = (server_dict[server_id]['Status'] if server_id != '' else vnf['status'])
        vnf_dict[vnf['id']]['host'] = (server_dict[server_id]['host'] if server_id != '' else 'None')

    ret = {'networks': net_dict, 'hosts': host_dict, 'vnfs': vnf_dict}
    return JsonResponse(ret)


@login_required
def networks_table(request):
    if request.method == 'POST':
        return HttpResponse(request)

    context = dict()
    context['networks'] = list_networks()['result']

    return HttpResponse(loader.get_template('networks_table.html').render(context, request))


@login_required
def create_sfc_form(request):
    if request.method == 'POST':
        sfc_form = SFCForm(request.POST)
        if sfc_form.is_valid():
            sfc_name = sfc_form.cleaned_data['sfc_name']
            vnf_list = sfc_form.cleaned_data['vnfs'].split('&')
            vnf_list = [vnf.replace('[]=','-') for vnf in vnf_list]
            r = create_sfc(sfc_name, vnf_list)
            message = ((r['result']['message'] + '\n') if 'message' in r['result'] else '') + r['error']
            return HttpResponse(message, content_type="text/plain")
    context = dict()
    context['vnfs'] = list_vnfs()['result']

    return HttpResponse(loader.get_template('create_sfc.html').render(context, request))


@login_required
def create_vnfd_form(request):
    if request.method == 'POST':
        vnfd_name = request.POST['vnfd_name']
        description = request.POST['description']
        image = request.POST['image']
        node = request.POST['node']
        network = request.POST['network']
        flavor = request.POST['flavor']
        vnfd_dict = {"template_name": vnfd_name + "-vnfd",
                     "description": description,
                     "service_properties": {
                       "Id": vnfd_name + "-vnfd",
                       "vendor": "tacker",
                       "version": 1,
                       "type": [
                         vnfd_name + "-vnf"
                       ]
                     },
                     "vdus": {
                       "vdu1": {
                         "id": "vdu1",
                         "vm_image": image,
                         "instance_type": flavor,
                         "service_type": vnfd_name + "-vnf",
                         "network_interfaces": {
                           "management": {
                             "network": network,
                             "management": True
                           }
                         },
                         "placement_policy": {
                           "availability_zone": "nova:"+node
                         },
                         "auto-scaling": "noop",
                         "monitoring_policy": "noop",
                         "failure_policy": "respawn",
                         "config": {
                           "param0": "key0",
                           "param1": "key1"
                         }
                       }
                      }
                     }
        r = create_vnfd(vnfd_dict)
        message = ((r['result']['message'] + '\n') if 'message' in r['result'] else '') + r['error']
        return HttpResponse(message, content_type="text/plain")

    context = dict()
    context['images'] = list_images()['result']
    context['nodes'] = list_nodes()['result']
    context['networks'] = list_networks()['result']
    context['flavors'] = list_flavors()['result']

    return HttpResponse(loader.get_template('create_vnfd.html').render(context, request))


@login_required
def create_vnf_form(request):
    if request.method == 'POST':
        vnf_form = VNFForm(request.POST)
        if vnf_form.is_valid():
            vnf_name = vnf_form.cleaned_data['vnf_name']
            vnfd_id  = vnf_form.cleaned_data['vnfd_id']
            r = create_vnf(vnf_name, vnfd_id)
            message = ((r['result']['message'] + '\n') if 'message' in r['result'] else '') + r['error']
            return HttpResponse(message, content_type="text/plain")
        return HttpResponse(vnf_form)

    context = dict()
    context['vnfds'] = list_vnfds()['result']

    return HttpResponse(loader.get_template('create_vnf.html').render(context, request))


@login_required
def create_vm_form(request):
    if request.method == 'POST':
        return HttpResponse(request)

    context = dict()
    context['images'] = list_images()['result']
    context['nodes'] = list_nodes()['result']
    context['networks'] = list_networks()['result']
    context['flavors'] = list_flavors()['result']

    return HttpResponse(loader.get_template('create_vm.html').render(context, request))


@login_required
def create_classifier_form(request):
    if request.method == 'POST':
        classifier_form = ClassifierForm(request.POST)
        #return HttpResponse(classifier_form)
        if classifier_form.is_valid():
            classifier_name = classifier_form.cleaned_data['classifier_name']
            src_port = classifier_form.cleaned_data['src_port']
            dst_port = classifier_form.cleaned_data['dst_port']
            netproto = classifier_form.cleaned_data['netproto']
            sfc_id    = classifier_form.cleaned_data['sfc_id']
            r = create_classifier(classifier_name, sfc_id, src_port, dst_port, netproto)
            message = ((r['result']['message'] + '\n') if 'message' in r['result'] else '') + r['error']
            return HttpResponse(message, content_type="text/plain")
        return HttpResponse(classifier_form)

    context = dict() 
    return HttpResponse(loader.get_template('create_classifier.html').render(context, request))


@login_required
def create_network_form(request):
    if request.method == 'POST':
        net_form = NetworkForm(request.POST)
        if net_form.is_valid():
            net_name = net_form.cleaned_data['net_name']
            net_cidr = net_form.cleaned_data['net_cidr']
            net_dns = net_form.cleaned_data['net_dns']
            net_dhcp_start = net_form.cleaned_data['net_dhcp_start']
            net_dhcp_end = net_form.cleaned_data['net_dhcp_end']
            r = create_network(net_name, net_cidr, net_dns, net_dhcp_start, net_dhcp_end)
            message = ''
            for k, i in r.iteritems():
                message += k + ':\n' + \
                           '-' * (len(k)+1) + '\n' + \
                           ((i['result']['message'] + '\n') if 'message' in i['result'] else '') + \
                           i['error'] + '\n\n'
            return HttpResponse(message, content_type="text/plain")
    context = dict()
    return HttpResponse(loader.get_template('create_network.html').render(context, request))


@login_required
def index(request):
    vnf_dict = {} #key = vnf id
    for vnf in list_vnfs()['result']:
        vnf_dict[vnf['id']] = vnf
        #Uncomment next line for extended vnf attributes (slow)
        #vnf_dict[vnf['id']].update(show_vnf(vnf['name'])['result'])

    classifier_dict = {} #key=sfc id
    for classifier in list_classifiers()['result']:
        classifier.update(show_classifier(classifier['id'])['result'])
        classifier_dict[classifier['chain']] = classifier

    sfc_list = list_sfcs()['result']
    for i in range(len(sfc_list)):
        vnfs = ''
        sfc_list[i].update(show_sfc(sfc_list[i]['name'])['result'])
        for j in range(len(sfc_list[i]['chain'])):
            sfc_list[i]['chain'][j] = vnf_dict[sfc_list[i]['chain'][j]]
            vnfs += ', ' + sfc_list[i]['chain'][j]['name']
        if len(vnfs) > 2: sfc_list[i][u'vnfs'] = vnfs[2:]
        if sfc_list[i]['id'] in classifier_dict:
            sfc_list[i][u'classifier'] = classifier_dict[sfc_list[i]['id']]
            sfc_list[i][u'classifier'][u'chain'] = sfc_list[i]['name']
            sfc_list[i][u'classifier'][u'acl_match_criteria'] = str(sfc_list[i][u'classifier'][u'acl_match_criteria']).replace("u'","'")
        else:
            sfc_list[i][u'classifier'] = {}

    context = {'sfc_list': sfc_list}
    return HttpResponse(loader.get_template('index.html').render(context, request))


@login_required
def deleteJSON(request):
    ret = {'result': 'Invalid request.'}
    if ('objtype' in request.POST) and ('objid' in request.POST):
        if request.POST['objtype'] == 'sfc':
            r = delete_sfc(request.POST['objid'])
            ret['result'] = (((r['result']['message']) if 'message' in r['result'] else '') + r['error']).replace('\n', ' ')
        elif request.POST['objtype'] == 'vnf':
            r = delete_vnf(request.POST['objid'])
            ret['result'] = (((r['result']['message']) if 'message' in r['result'] else '') + r['error']).replace('\n', ' ')
        elif request.POST['objtype'] == 'vnfd':
            r = delete_vnfd(request.POST['objid'])
            ret['result'] = (((r['result']['message']) if 'message' in r['result'] else '') + r['error']).replace('\n', ' ')
        elif request.POST['objtype'] == 'classifier':
            r = delete_classifier(request.POST['objid'])
            ret['result'] = (((r['result']['message']) if 'message' in r['result'] else '') + r['error']).replace('\n', ' ')
        elif request.POST['objtype'] == 'network':
            r = delete_network(request.POST['objid'])
            ret['result'] = (((r['network']['result']['message']) if 'message' in r['network']['result'] else '') + r['network']['error']).replace('\n', ' ')

    return JsonResponse(ret)
