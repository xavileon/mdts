# Copyright 2015 Midokura SARL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
