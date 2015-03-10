from mdts2.framework.host import Host
from mdts2.framework.neutron import get_neutron_client

#from neutronclient.neutron import client

from mock import Mock
from mock import patch

@patch('mdts2.framework.host.neutron')
def test_host_create_vm(mock_neutron):
    subnet =  {'subnet': {
                    'name': 'test-l2',
                    'enable_dhcp': True,
                    'network_id': 'b6c86193-024c-4aeb-bd9c-ffc747bb8a74',
                    'tenant_id': 'mdts2-ft2015-03-10 06:03:17',
                    'dns_nameservers': [],
                    'ipv6_ra_mode': None,
                    'allocation_pools': [{
                        'start': '1.1.1.2',
                        'end': '1.1.1.254'}],
                    'gateway_ip': '1.1.1.1',
                    'ipv6_address_mode': None,
                    'ip_version': 4,
                    'host_routes': [],
                    'cidr': '1.1.1.0/24',
                    'id': '6c838ffc-6a40-49ba-b363-6380b0a7dae6'}}

    h = Host()
    h._bind_port = Mock(return_value=True)
    h._unbind_port = Mock(return_value=True)
    mock_neutron.show_subnet = Mock(return_value=subnet)

    mac = 'fa:16:3e:68:a7:df'
    ip_addr = '1.1.1.2'
    port = {'port':{
                'status': 'ACTIVE',
                'binding:host_id': None,
                'name': '',
                'admin_state_up': True,
                'network_id': '0c05d77e-96ce-4e04-841b-5a07b7815c8a',
                'tenant_id': 'devilman-2015-03-08 12:19:59',
                'binding:vif_details': {'port_filter': True},
                'binding:vnic_type': 'normal',
                'binding:vif_type': 'midonet',
                'device_owner': '',
                'mac_address': mac,
                'fixed_ips': [
                    {'subnet_id': '74ad2fcd-7a95-4b59-93d3-a20de1c5480b',
                     'ip_address': ip_addr}],
                'id': 'fe6707e3-9c99-4529-b059-aa669d1463bb',
                'security_groups': ['9be76a64-4bed-4b6e-833b-17273b62908b'],
                'device_id': ''}}



    vm = h.create_vm('ika', port)
    try:
        vm.execute('ip link show dev eth0 | grep  %s' % mac)
        vm.execute('ip addr show dev eth0 | grep  %s' % ip_addr)
    except Exception as e:
        print e.output
        raise AssertionError('veth inside netns does not have correct mac')
    vm.delete()
