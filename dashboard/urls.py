from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^create-sfc/', views.create_sfc_form, name='create_sfc'),
    url(r'^create-vnfd/', views.create_vnfd_form, name='create_vnfd'),
    url(r'^create-vnf/', views.create_vnf_form, name='create_vnf'),
    url(r'^create-classifier/', views.create_classifier_form, name='create_classifier'),
    url(r'^create-network/', views.create_network_form, name='create_network'),
    url(r'^create-vm/', views.create_vm_form, name='create_vm'),
    url(r'^vnfs/', views.vnfs_table, name='vnfs_table'),
    url(r'^vnfds/', views.vnfds_table, name='vnfds_table'),
    url(r'^networks/', views.networks_table, name='networks_table'),
    url(r'^delete/', views.deleteJSON, name='deleteJSON'),
    url(r'^mapdata/', views.networksJSON, name='networksJSON'),
]
