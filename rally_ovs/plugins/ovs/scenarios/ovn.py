# Copyright 2016 Ebay Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from rally_ovs.plugins.ovs import scenario
from rally.task import atomic
from rally.common import logging
from rally import exceptions
from rally_ovs.plugins.ovs.utils import get_random_sandbox
from rally_ovs.plugins.ovs import utils
import netaddr

LOG = logging.getLogger(__name__)



class OvnScenario(scenario.OvsScenario):


    RESOURCE_NAME_FORMAT = "lswitch_XXXXXX_XXXXXX"


    '''
    return: [{"name": "lswitch_xxxx_xxxxx", "cidr": netaddr.IPNetwork}, ...]
    '''
    @atomic.action_timer("ovn.create_lswitch")
    def _create_lswitches(self, lswitch_create_args, num_switches=-1):

        print("create lswitch")
        self.RESOURCE_NAME_FORMAT = "lswitch_XXXXXX_XXXXXX"
        self.port_mac = dict()

        if (num_switches == -1):
            num_switches = lswitch_create_args.get("amount", 1)
        batch = lswitch_create_args.get("batch", num_switches)

        start_cidr = lswitch_create_args.get("start_cidr", "")
        if start_cidr:
            start_cidr = netaddr.IPNetwork(start_cidr)

        LOG.info("Create lswitches method: %s" % self.install_method)
        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox", self.install_method)
        ovn_nbctl.enable_batch_mode()

        flush_count = batch
        lswitches = []
        for i in range(num_switches):
            name = self.generate_random_name()

            lswitch = ovn_nbctl.lswitch_add(name)
            if start_cidr:
                lswitch["cidr"] = start_cidr.next(i)

            LOG.info("create %(name)s %(cidr)s" % \
                      {"name": name, "cidr":lswitch["cidr"]})
            lswitches.append(lswitch)

            flush_count -= 1
            if flush_count < 1:
                ovn_nbctl.flush()
                flush_count = batch

        ovn_nbctl.flush() # ensure all commands be run
        ovn_nbctl.enable_batch_mode(False)
        return lswitches


    @atomic.optional_action_timer("ovn.list_lswitch")
    def _list_lswitches(self):
        print("list lswitch")
        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox")
        ovn_nbctl.enable_batch_mode(False)
        ovn_nbctl.lswitch_list()

    @atomic.action_timer("ovn.delete_lswitch")
    def _delete_lswitch(self, lswitches):
        print("delete lswitch")
        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox")
        ovn_nbctl.enable_batch_mode()
        for lswitch in lswitches:
            ovn_nbctl.lswitch_del(lswitch["name"])

        ovn_nbctl.flush()


    def _get_or_create_lswitch(self, lswitch_create_args=None):
        pass

    @atomic.action_timer("ovn.create_lport")
    def _create_lports(self, lswitch, lport_create_args = [], lport_amount=1):
        LOG.info("create %d lports on lswitch %s" % \
                            (lport_amount, lswitch["name"]))

        self.RESOURCE_NAME_FORMAT = "lport_XXXXXX_XXXXXX"

        batch = lport_create_args.get("batch", lport_amount)

        LOG.info("Create lports method: %s" % self.install_method)
        install_method = self.install_method

        network_cidr = lswitch.get("cidr", None)
        ip_addrs = None
        if network_cidr:
            end_ip = network_cidr.ip + lport_amount
            if not end_ip in network_cidr:
                message = _("Network %s's size is not big enough for %d lports.")
                raise exceptions.InvalidConfigException(
                            message  % (network_cidr, lport_amount))

            ip_addrs = netaddr.iter_iprange(network_cidr.ip, network_cidr.last)

        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox", install_method)
        ovn_nbctl.enable_batch_mode()

        base_mac = [i[:2] for i in self.task["uuid"].split('-')]
        base_mac[0] = str(hex(int(base_mac[0], 16) & 254))
        base_mac[3:] = ['00']*3

        flush_count = batch
        lports = []
        LOG.info("------> flush_count or batch: %d", flush_count)
        for i in range(lport_amount):
            LOG.info("------> Create port idx: %d", i)
            name = self.generate_random_name()
            lport = ovn_nbctl.lswitch_port_add(lswitch["name"], name)

            ip = str(ip_addrs.next()) if ip_addrs else ""
            mac = utils.get_random_mac(base_mac)

            ovn_nbctl.lport_set_addresses(name, [mac, ip])
            # ovn_nbctl.lport_set_addresses(name, [mac])
            ovn_nbctl.lport_set_port_security(name, mac)
            # self.port_mac[name] = mac

            lports.append(lport)

            flush_count -= 1
            if flush_count < 1:
                LOG.info("------> Flush cmd")
                ovn_nbctl.flush()
                flush_count = batch

        ovn_nbctl.flush()  # ensure all commands be run
        ovn_nbctl.enable_batch_mode(False)
        return lports


    @atomic.action_timer("ovn.delete_lport")
    def _delete_lport(self, lports):
        print("delete lport")
        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox")
        ovn_nbctl.enable_batch_mode()
        for lport in lports:
            ovn_nbctl.lport_del(lport["name"])

        ovn_nbctl.flush()


    @atomic.action_timer("ovn.action_timer")
    def _list_lports(self, lswitches, install_method = "sandbox"):
        print("list lports")
        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox", install_method)
        ovn_nbctl.enable_batch_mode(False)
        for lswitch in lswitches:
            LOG.info("list lports on lswitch %s" % lswitch["name"])
            ovn_nbctl.lport_list(lswitch["name"])



    @atomic.action_timer("ovn.create_acl")
    def _create_acl(self, lswitch, lports, acl_create_args, acls_per_port):
        sw = lswitch["name"]
        LOG.info("create %d ACLs on lswitch %s" % (acls_per_port, sw))

        direction = acl_create_args.get("direction", "to-lport")
        priority = acl_create_args.get("priority", 1000)
        action = acl_create_args.get("action", "allow")

        if direction == "from-lport":
            p = "inport"
        else:
            p = "outport"

        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox", self.install_method)
        ovn_nbctl.enable_batch_mode()
        for lport in lports:
            for i in range(acls_per_port):
                match = '%s == "%s" && ip4 && udp && udp.src == %d' % \
                        (p, lport["name"], 100 + i)
                ovn_nbctl.acl_add(sw, direction, priority, match, action)

            ovn_nbctl.flush()


    @atomic.action_timer("ovn.list_acl")
    def _list_acl(self, lswitches):
        LOG.info("list ACLs")
        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox", self.install_method)
        ovn_nbctl.enable_batch_mode(False)
        for lswitch in lswitches:
            LOG.info("list ACLs on lswitch %s" % lswitch["name"])
            ovn_nbctl.acl_list(lswitch["name"])


    @atomic.action_timer("ovn.delete_acl")
    def _delete_acl(self, lswitches):
        LOG.info("delete ACLs")

        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox")
        ovn_nbctl.enable_batch_mode(True)
        for lswitch in lswitches:
            LOG.info("delete ACLs on lswitch %s" % lswitch["name"])
            ovn_nbctl.acl_del(lswitch["name"])

        ovn_nbctl.flush()

    @atomic.action_timer("ovn_network.create_routers")
    def _create_routers(self, router_create_args):

        LOG.info("Create Logical routers")
        self.RESOURCE_NAME_FORMAT = "lrouter_XXXXXX_XXXXXX"

        amount = router_create_args.get("amount", 1)
        batch = router_create_args.get("batch", 1)

        LOG.info("Create lrouters method: %s" % self.install_method)
        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox", self.install_method)
        ovn_nbctl.enable_batch_mode()

        flush_count = batch
        lrouters = []

        for i in range(amount):
            name = self.generate_random_name()

            lrouter = ovn_nbctl.lrouter_add(name)

            LOG.info("create %s" % name)
            lrouters.append(lrouter)

            flush_count -= 1
            if flush_count < 1:
                ovn_nbctl.flush()
                flush_count = batch

        ovn_nbctl.flush() # ensure all commands be run
        ovn_nbctl.enable_batch_mode(False)

        return lrouters

    # ovn-nbctl lrp-add R1 ls1 00:00:00:01:02:f1 192.168.1.1/24
    # ovn-nbctl lsp-add ls1 rp-ls1 -- set Logical_Switch_Port rp-ls1 \
    #           type=router options:router-port=ls1 addresses=\"00:00:00:01:02:f1\"
    def _connect_network_to_router(self, router, network):
        LOG.info("Connect network %s to router %s" % (network["name"], router["name"]))

        ovn_nbctl = self.controller_client("ovn-nbctl")
        install_method = self.install_method
        ovn_nbctl.set_sandbox("controller-sandbox", install_method)
        ovn_nbctl.enable_batch_mode(False)

        LOG.info("1. Add router port %s to router %s" % (network["name"], router["name"]))

        base_mac = [i[:2] for i in self.task["uuid"].split('-')]
        base_mac[0] = str(hex(int(base_mac[0], 16) & 254))
        base_mac[3:] = ['00']*3
        mac = utils.get_random_mac(base_mac)
        LOG.info("base_mac addr:  %s" % (base_mac))
        LOG.info("mac addr:  %s" % (mac))
        lrouter_port = ovn_nbctl.lrouter_port_add(router["name"], network["name"], mac,
                                                  str(network["cidr"]))
        ovn_nbctl.flush()


        switch_router_port = "rp-" + network["name"]
        LOG.info("2. Add router switch port %s to switch %s" % (switch_router_port, network["name"]))
        lport = ovn_nbctl.lswitch_port_add(network["name"], switch_router_port)
        ovn_nbctl.db_set('Logical_Switch_Port', switch_router_port,
                         ('options', {"router_port":network["name"]}),
                         ('type', 'router'),
                         ('address', "\\"+"\""+mac+"\\"+"\""))
        ovn_nbctl.flush()


    # NOTE(huikang): num_networks overides the "amount" in network_create_args
    @atomic.action_timer("ovn_network.create_network")
    def _create_networks(self, network_create_args, num_networks=-1):
        physnet = network_create_args.get("physical_network", None)
        lswitches = self._create_lswitches(network_create_args, num_networks)
        batch = network_create_args.get("batch", len(lswitches))

        batch = network_create_args.get("batch", 1)

        LOG.info("Create network method: %s" % self.install_method)
        LOG.info("Batch: %s" % batch)
        if physnet != None:
            ovn_nbctl = self.controller_client("ovn-nbctl")
            ovn_nbctl.set_sandbox("controller-sandbox", self.install_method)
            ovn_nbctl.enable_batch_mode()

            flush_count = batch
            for lswitch in lswitches:
                network = lswitch["name"]
                LOG.info("Set address for network: %s" % network)
                port = "provnet-%s" % network
                ovn_nbctl.lswitch_port_add(network, port)
                ovn_nbctl.lport_set_addresses(port, ["unknown"])
                ovn_nbctl.lport_set_type(port, "localnet")
                ovn_nbctl.lport_set_options(port, "network_name=%s" % physnet)

                flush_count -= 1
                if flush_count < 1:
                    ovn_nbctl.flush()
                    LOG.info("Flush commands")
                    flush_count = batch

            ovn_nbctl.flush()

        return lswitches

    @atomic.action_timer("ovn_network.of_check_port")
    def _of_check_ports(self, lports, sandboxes, port_bind_args):
        port_bind_args = port_bind_args or {}
        wait_up = port_bind_args.get("wait_up", False)

        sandbox_num = len(sandboxes)
        lport_num = len(lports)
        lport_per_sandbox = (lport_num + sandbox_num - 1) / sandbox_num

        LOG.info("Checking OF lports method: %s" % self.install_method)
        install_method = self.install_method

        j = 0
        for i in range(0, len(lports), lport_per_sandbox):
            lport_slice = lports[i:i+lport_per_sandbox]

            sandbox = sandboxes[j]["name"]
            farm = sandboxes[j]["farm"]
            ovs_vsctl = self.farm_clients(farm, "ovs-vsctl")
            ovs_vsctl.set_sandbox(sandbox, install_method)
            ovs_vsctl.enable_batch_mode()

            for lport in lport_slice:
                port_name = lport["name"]

                LOG.info("of check %s to %s on %s" % (port_name, sandbox, farm))

                # check if OF rules installed correctly
                mac_addr = self.port_mac[port_name]
                LOG.info("MAC address: %s" % mac_addr)
                of_check = ovs_vsctl.of_check('br-int', port_name, mac_addr)
                if of_check is False:
                    LOG.info("Return false" )
                    raise exceptions.NotFoundException(message="openflow rule")

            ovs_vsctl.flush()
            j += 1

    @atomic.action_timer("ovn_network.bind_port")
    def _bind_ports(self, lports, sandboxes, port_bind_args):
        port_bind_args = port_bind_args or {}
        wait_up = port_bind_args.get("wait_up", False)
        # "wait_sync" takes effect only if wait_up is True.
        # By default we wait for all HVs catching up with the change.
        wait_sync = port_bind_args.get("wait_sync", "hv")
        if wait_sync.lower() not in ['hv', 'sb', 'none']:
            raise exceptions.InvalidConfigException(_(
                "Unknown value for wait_sync: %s. "
                "Only 'hv', 'sb' and 'none' are allowed.") % wait_sync)

        sandbox_num = len(sandboxes)
        lport_num = len(lports)
        lport_per_sandbox = (lport_num + sandbox_num - 1) / sandbox_num

        LOG.info("Bind lports method: %s" % self.install_method)
        install_method = self.install_method

        j = 0
        for i in range(0, len(lports), lport_per_sandbox):
            lport_slice = lports[i:i+lport_per_sandbox]

            sandbox = sandboxes[j]["name"]
            farm = sandboxes[j]["farm"]
            ovs_vsctl = self.farm_clients(farm, "ovs-vsctl")
            ovs_vsctl.set_sandbox(sandbox, install_method)
            ovs_vsctl.enable_batch_mode()
            for lport in lport_slice:
                port_name = lport["name"]

                LOG.info("bind %s to %s on %s" % (port_name, sandbox, farm))

                ovs_vsctl.add_port('br-int', port_name)
                ovs_vsctl.db_set('Interface', port_name,
                                 ('external_ids', {"iface-id":port_name,
                                                   "iface-status":"active"}),
                                 ('admin_state', 'up'))

            ovs_vsctl.flush()
            j += 1

        if wait_up:
            self._wait_up_port(lports, wait_sync, install_method)
        ovs_vsctl.flush()

        # check OF for all the bound ports
        #ovn_nbctl = self.controller_client("ovn-nbctl")
        #ovn_nbctl.set_sandbox("controller-sandbox", self.install_method)
        #ovn_nbctl.disable_batch_mode()


    @atomic.action_timer("ovn_network.wait_port_up")
    def _wait_up_port(self, lports, wait_sync, install_method):
        LOG.info("wait port up. sync: %s" % wait_sync)
        ovn_nbctl = self.controller_client("ovn-nbctl")
        ovn_nbctl.set_sandbox("controller-sandbox", install_method)
        ovn_nbctl.enable_batch_mode(True)

        for lport in lports:
            ovn_nbctl.wait_until('Logical_Switch_Port', lport["name"], ('up', 'true'))

        if wait_sync != "none":
            ovn_nbctl.sync(wait_sync)





