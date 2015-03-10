# Copyright 2014 Midokura SARL
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

import logging
import subprocess

LOG = logging.getLogger(__name__)


class VM(object):


    def __init__(self, name, port, host):
        """
        :prarm name: name of the psedo VM, used for netns and host's veth name
        :pram host: back referene to host

        """
        self._name = name
        self._port = port
        self._host = host

    def delete(self):
        self._host.delete_vm(self._name, self._port)


    def execute(self, cmdline, timeout=None):
        """Executes cmdline inside VM

        Args:
            cmdline: command line string that gets executed in this VM
            timeout: timeout in second

        Returns:
            output as a bytestring


        Raises:
            subprocess.CalledProcessError: when the command exists with non-zero
                                           value, including timeout.
            OSError: when the executable is not found or some other error
                     invoking
        """

        LOG.debug('VM: executing command: %s', cmdline)


        cmdline = "ip netns exec %s %s" % (
            self._name, ('timeout %d ' % timeout if timeout else "")  + cmdline)

        try:
            result = subprocess.check_output(cmdline, shell=True)
            LOG.debug('Result=%r', result)
        except subprocess.CalledProcessError as e:
            print 'command output: ',   e.output
            raise

        return result


    def expect(self, pcap_filter_string, timeout):
        """
        Expects packet with pcap_filter_string with tcpdump.
        See man pcap-filter for more details as to what you can match.


        Args:
            pcap_filter_string: capture filter to pass to tcpdump
                                See man pcap-filter
            timeout: in second

        Returns:
            True: when packet arrives
            False: when packet doesn't arrive within timeout
        """

        count = 1
        cmdline = 'timeout %s tcpdump -n -l -i eth0 -c %s %s 2>&1' % (
            timeout,
            count, pcap_filter_string)

        try:
            output = self.execute(cmdline)
            retval = True
            for l in output.split('\n'):
                LOG.debug('output=%r', l)
        except subprocess.CalledProcessError as e:
            print 'OUTPUT: ', e.output
            LOG.debug('expect failed=%s', e)
            retval = False
        LOG.debug('Returning %r', retval)
        return retval

    def send_arp_request(self, target_ipv4):
        cmdline = 'mz eth0 -t arp "request, targetip=%s"' % target_ipv4
        LOG.debug("cmdline: %s" % cmdline)
        return self.execute(cmdline)

    def send_arp_reply(self, src_mac, target_mac, src_ipv4, target_ipv4):
        arp_msg = '"' + "reply, smac=%s, tmac=%s, sip=%s, tip=%s" %\
        (src_mac, target_mac, src_ipv4, target_ipv4) + '"'
        mz_cmd = ['mz', 'eth0', '-t', 'arp', arp_msg]
        return self.execute(mz_cmd)

    def clear_arp(self):
        cmdline = 'ip neigh flush all'
        LOG.debug('VM: flushing arp cache: ' + cmdline)
        self.execute(cmdline)

    def set_ifup(self):
        return self.execute('ip link set eth0 up')

    def set_ifdown(self):
        return self.execute('ip link set eth0  down')

    def set_ipv4_addr(self, ipv4_addr):
        return self.execute('ip addr add %s dev eth0' % ipv4_addr)

    def set_ipv4_gw(self, gw):
        return self.execute('ip route add default via %s' % gw)

    def assert_pings_to(self, other, count=3):
        """
        Asserts that the sender VM can ping to the other VM

        :param other: ping target VM instance
        """


        sender = self._port['port'].get('fixed_ips')
        receiver = other._port['port'].get('fixed_ips')
        if sender and receiver:
            receiver_ip = receiver[0]['ip_address']
            try:
                self.execute('ping -c %s %s' % (count, receiver_ip))
            except:
                raise AssertionError(
                        'ping from %s to %s failed'% (self, other))

    def  __repr__(self):
        return 'VM(%s)(port_id=%s)' % (self._name, self._port['port']['id'])




