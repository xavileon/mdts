#!/usr/bin/env python

import logging
from datetime import datetime
from neutronclient.neutron import client

from mdts2.framework.host import Host
from mdts2.framework.neutron import get_neutron_client
from mdts2.framework.neutron import nuke


logging.basicConfig(level=logging.DEBUG)
neutron = get_neutron_client()

# list of virtual hosts(currently hardcoded for devstack-lite setup)
hosts = [Host()]

def setup():
    nuke()

def teardown():
    pass

def test_ping_between_two_vms():
    #
    # Title: basic L2 connectivity in Neutron network
    #
    # When: there is a neutron network on which there are 2 neutron ports
    # Then: spwan VMs for each port
    # Then: VMs can ping to each other
    #
    # Virtual Topology:
    #
    # TODO: visualize the topology
    #


    test_id = 'mdts2_test_ping_between_two_vms' + datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')
    logging.info('Starting a test %s', test_id)


    tenant_id = test_id
    name = 'test_ping_between_two_vms'

    #
    # Topology setup
    #

    # create network and subnet
    net_data = {'name': name, 'tenant_id': tenant_id}
    net = neutron.create_network({'network':net_data})

    network_id = net['network']['id']

    subnet = neutron.create_subnet(
            {'subnet': {'name': name,
                        'tenant_id': tenant_id,
                        'cidr':'1.1.1.0/24',
                        'network_id': network_id,
                        'ip_version': 4}  })

    # create two ports
    port1 = neutron.create_port(
            {'port': {'tenant_id': tenant_id,
                'network_id': network_id}})

    port2 = neutron.create_port(
            {'port': {'tenant_id': tenant_id,
                'network_id': network_id}})

    # create two VMs on host[0] for each port
    vm1 = hosts[0].create_vm('vm1', port1)
    vm2 = hosts[0].create_vm('vm2', port2)

    # Test:
    # make sure that vm1 cna vm2 can ping each other
    #
    vm1.assert_pings_to(vm2)
    vm2.assert_pings_to(vm1)

    #
    # teardown VMs and neutron
    #
    vm1.delete()
    vm2.delete()

    # tearing down neutron ports and network
    neutron.delete_port(port1['port']['id'])
    neutron.delete_port(port2['port']['id'])
    neutron.delete_network(network_id)

