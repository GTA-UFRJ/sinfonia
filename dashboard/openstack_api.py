# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
import json


def get_auth_token(json_file, keystone_url):
	""" Get authentication token from Keystone API """
	with open(json_file) as file:
		auth_payload = json.load(file)
	headers = {'Content-type': 'application/json'}
	r = requests.post(keystone_url, headers=headers, data=json.dumps(auth_payload))
	return r.headers['X-Subject-Token']


def get_api_version(tacker_url):
	""" Get Tacker API version """
	r = requests.get(tacker_url[:-4])
	return r


def list_vnfs(auth_token, tacker_url):
	""" List VNFs for the user associated with auth_token """
	headers = {'X-Auth-Token': auth_token}
	r = requests.get(tacker_url + '/vnfs', headers=headers)
	return r


def list_vnfs2(auth_token, tacker_url):
	""" List VNFs for the user associated with auth_token """
	headers = {'X-Auth-Token': auth_token}
	r = requests.get("http://10.240.114.132:8090/exec?tacker vnf-list | grep 'gta-vnf-' | awk '{print $4}'")
	return r


def list_vnfds(auth_token, tacker_url):
	""" List VNFDs for the user associated with auth_token """
	headers = {'X-Auth-Token': auth_token}
	r = requests.get(tacker_url + '/vnfds', headers=headers)
	return r


def list_sfcs(auth_token, tacker_url):
	""" List SFCs for the user associated with auth_token """
	headers = {'X-Auth-Token': auth_token}
	r = requests.get(tacker_url + '/sfcs', headers=headers)
	return r


# API dos classificadores não funciona ):
def list_classifiers(auth_token, tacker_url):
	""" List classifiers for the user associated with auth_token """
	headers = {'X-Auth-Token': auth_token}
	r = requests.get(tacker_url + '/classifiers', headers=headers)
	return r


def show_vnf(auth_token, tacker_url, vnf_id):
	""" Show detailed info on the VNF identified by sfc_id """
	headers = {'X-Auth-Token': auth_token}
	r = requests.get(tacker_url + '/vnfs/' + vnf_id, headers=headers)
	return r


def show_vnfd(auth_token, tacker_url, vnfd_id):
	""" Show detailed info on the VNFD identified by sfc_id """
	headers = {'X-Auth-Token': auth_token}
	r = requests.get(tacker_url + '/vnfds/' + vnfd_id, headers=headers)
	return r


def show_sfc(auth_token, tacker_url, sfc_id):
	""" Show detailed info on the SFC identified by sfc_id """
	headers = {'X-Auth-Token': auth_token}
	r = requests.get(tacker_url + '/sfcs/' + sfc_id, headers=headers)
	return r


# API dos classificadores não funciona ):
def show_classifier(auth_token, tacker_url, classifier_id):
	""" Show detailed info on the classifier identified by classiftacker%20vnf-ier_id """
	headers = {'X-Auth-Token': auth_token}
	r = requests.get(tacker_url + '/classifiers/' + classifier_id, headers=headers)
	return r