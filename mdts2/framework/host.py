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


import subprocess
from mdts2.framework.vm import VM
from mdts2.framework.neutron import get_neutron_client

neutron = get_neutron_client()

class Host:
    """
    A class to wrap Compute/Midolman host.
    """

    def __init__(self, netns=None):
        """
            :param netns: netns name of compute/midolman host. None for
                          devstack or allinone deployment.
        """
        self._netns = netns
        self._vms = {}


    def create_vm(self, name, port, setup_ip=True):
        """ Creates a pseudo VM based on netns for neutron port.
            This involves the following steps:
                1. create a netns with the same name as name
                2. create a veth pair
                3. stick vethB to the netns and configure (e.g. mac/ip adder)
                4. (if Host is running inside netns)
                      stick vethA to host's netns
                5. bind interface to MidoNet with mm-ctl

        :param name: name of VM: used for netns and net_device interface name
        :param port: Neutron Port data
        :param subnet: Neutron Subnet data
        :param setup_ip: configure ip addr and gw if True
        :returns VM instance
        """

        if self._vms.get(name):
            raise AssertionError('VM with the same name already exists')

        try:
            # create netns with the same name as name
            netns = name
            cmdline = 'ip netns add %(netns)s ' % {'netns': netns}
            subprocess.check_output(cmdline.split(), stderr=subprocess.STDOUT)

            # create veth pair
            peer_name = name + '-p'
            cmdline = ('ip link add %(name)s type veth peer name '
                       '%(peer_name)s' % { 'name': name,
                                           'peer_name': peer_name})
            subprocess.check_output(cmdline.split(), stderr=subprocess.STDOUT)

            # set the host side interface up
            cmdline = 'ip link set %(name)s up' % {'name': name}
            subprocess.check_output(cmdline.split(), stderr=subprocess.STDOUT)

            # stick the host side to the host's netns
            if self._netns:
                cmdline = 'ip link set %(name)s netns %(netns)s' % {
                    'name': name, 'host_netns': self._netns}
                subprocess.check_output(cmdline.split(),
                        stderr=subprocess.STDOUT)

            #
            # Now take care of netns side
            #

            # stick the peer side to the netns
            cmdline = 'ip link set %(peer_name)s netns %(name)s' % {
                    'name': name, 'peer_name': peer_name}
            subprocess.check_output(cmdline.split(), stderr=subprocess.STDOUT)

            # rename it to eth0
            cmdline =('ip netns exec %(netns)s ip link set dev %(peer_name)s '
                      'name eth0' % {'netns': netns, 'peer_name': peer_name})
            subprocess.check_output(cmdline.split(), stderr=subprocess.STDOUT)

            vm = VM(name, port, self)
            self._vms[name] = vm
            # set it up
            vm.set_ifup()

            # configure ip/gw
            if setup_ip:
                fixed_ips = port['port'].get('fixed_ips')
                for fixed in fixed_ips:
                    ipv4_addr = fixed['ip_address']
                    subnet_id = fixed['subnet_id']

                    subnet = neutron.show_subnet(subnet_id)
                    prefix = subnet['subnet']['cidr'].split('/')[1]
                    gateway_ip = subnet['subnet'].get('gateway_ip')

                    vm.set_ipv4_addr(ipv4_addr + '/' + prefix)
                    if gateway_ip:
                        vm.set_ipv4_gw(gateway_ip)


            # configure mac address
            mac = port.get('port').get('mac_address')
            vm.execute('ip link set eth0 address %(mac)s' % {'mac': mac})

            # Now bind it to MidoNet
            port_id = port['port']['id']
            self._bind_port(port_id, name)

        except subprocess.CalledProcessError as e:
            print 'command output: ',   e.output
            raise
        else:
            return vm

    def delete_vm(self, name, port):
        """Deletes psedo VM

        :param name: name of the VM to delete
        """

        try:

            # delete veth pair
            cmdline = 'ip link del %s' % name
            subprocess.check_output(cmdline.split(), stderr=subprocess.STDOUT)

            # delete netns
            cmdline = 'ip netns del %s' % name
            subprocess.check_output(cmdline.split(), stderr=subprocess.STDOUT)

            # unbind MidoNet port
            port_id = port['port']['id']
            self._unbind_port(port_id)
        except subprocess.CalledProcessError as e:
            print 'command output: ',   e.output
            raise


    def _bind_port(self, port_id, ifname):
        cmdline = ''
        if self._netns:
            cmdline += 'ip netns exec %s" % self._netns '
        cmdline += 'mm-ctl --bind-port %(port_id)s %(ifname)s' % {
            'port_id': port_id, 'ifname': ifname}
        subprocess.check_output(cmdline.split(), stderr=subprocess.STDOUT)


    def _unbind_port(self, port_id):
        cmdline = ''
        if self._netns:
            cmdline += 'ip netns exec %s" % self._netns '
        cmdline += 'mm-ctl --unbind-port %s' % port_id
        subprocess.check_output(cmdline.split(), stderr=subprocess.STDOUT)


