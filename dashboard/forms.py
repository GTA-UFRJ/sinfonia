from django import forms


class SFCForm(forms.Form):
	sfc_name = forms.CharField(label='sfc_name')
	vnfs = forms.CharField(widget=forms.HiddenInput)


class NetworkForm(forms.Form):
	net_name, net_cidr, net_dns, net_dhcp_start, net_dhcp_end = (forms.CharField(),)*5


class VNFForm(forms.Form):
	vnf_name, vnfd_id = (forms.CharField(),)*2

class ClassifierForm(forms.Form):
	classifier_name, src_port, dst_port, netproto = (forms.CharField(),)*4
	sfc_id = forms.CharField(widget=forms.HiddenInput)

