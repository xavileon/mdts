from neutronclient.neutron import client

def get_neutron_client():
    return client.Client('2.0', endpoint_url='http://localhost:9696',
                         auth_strategy='noauth')

def nuke():
    """Wipes out all the neutron resources
    """

    neutron = get_neutron_client()
    ports = neutron.list_ports()
    for p in ports['ports']:
        neutron.delete_port(p['id'])

    networks = neutron.list_networks()
    for n in networks['networks']:
        neutron.delete_network(n['id'])
