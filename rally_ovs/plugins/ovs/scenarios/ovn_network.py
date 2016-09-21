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

import random
from rally.common import logging
from rally_ovs.plugins.ovs.scenarios import ovn

from rally import exceptions
from rally.task import scenario
from rally.task import validation

LOG = logging.getLogger(__name__)

class LogicalNetwork():
    def __init__(self):
        self.sandboxes = []
        self.ports_per_network = 0
        self.lswitch = None

    def set_lswitch(self, lswitch):
        self.lswitch = lswitch

    def add_sandbox(self, sandbox):
        self.sandboxes.append(sandbox)

    def get_lswitch(self):
        return self.lswitch

    def get_sandboxes(self):
        return self.sandboxes

    def get_ports_per_network(self):
        return self.ports_per_network



def initialize_logical_networks(lswitches):
    LOG.info("Initialize logical lswitches with %s" % lswitches)
    logical_networks = []

    for lswitch in lswitches:
        logical_network = LogicalNetwork()
        logical_network.set_lswitch(lswitch)
        LOG.info("Logical network: %s" % logical_network.get_lswitch())
        logical_networks.append(logical_network)

    LOG.info("In Logical networks: %s" % logical_networks[0].get_lswitch())
    return logical_networks

def allocate_networks_on_sandboxes_v2(logical_networks, sandboxes, chassis_per_network):
    LOG.info("Allocate networks on sandboxes")
    LOG.info("Chassis per network %s" % chassis_per_network)

    for network in logical_networks:
        LOG.info("Network: %s" % network.get_lswitch())

    LOG.info("Sanity check")

    # Sanity check
    num_networks = len(logical_networks)

    if (chassis_per_network > len(sandboxes)) or (chassis_per_network < 1):
        message = ("Invalid %d chassis_per_network; should be [0, %d]")
        raise exceptions.InvalidConfigException(
            message  % (chassis_per_network, len(sandboxes)))

    if chassis_per_network == len(sandboxes):
        LOG.info("Default allocation")
        for logical_network in logical_networks:
            for sandbox in sandboxes:
                logical_network.add_sandbox(sandbox)
    else:
        LOG.info("chassis per network: %s" % chassis_per_network)

        sandbox_set = []
        for i in range(0, len(sandboxes)):
            sandbox_set.append(i)
        LOG.info("Set: %s" % sandbox_set)

        for network in logical_networks:
            sandbox_ids = random.sample(sandbox_set, chassis_per_network)
            LOG.info("Selected set: %s" % sandbox_ids)
            for i in range(0, chassis_per_network):
                # sandbox_id = random.randint(0, len(sandboxes)-1)
                idx = sandbox_ids[i]
                LOG.info("random id: %d, sandbox %s" % (idx, sandboxes[idx]["name"]))
                network.add_sandbox(sandboxes[idx])

    return logical_networks


def allocate_networks_on_sandboxes(logical_networks, sandboxes, networks_per_sandbox=0):
    LOG.info("Allocate networks on sandboxes")

    LOG.info("Network per sandbox %s" % networks_per_sandbox)

    for network in logical_networks:
        LOG.info("Network: %s" % network.get_lswitch())

    if networks_per_sandbox == 0:
        for logical_network in logical_networks:
            for sandbox in sandboxes:
                logical_network.add_sandbox(sandbox)
    else:
        LOG.info("Sanity check")

        # Sanity check
        num_networks = len(logical_networks)

        if (num_networks % networks_per_sandbox) != 0 :
            message = ("Number of network %s is not divisible by network per sandbox %s")
            raise exceptions.InvalidConfigException(
                message  % (str(num_networks), str(networks_per_sandbox)))

        LOG.info("Number of networks: %s" % str(num_networks))
        num_network_groups = num_networks / networks_per_sandbox
        LOG.info("Number of network group: %s" % str(num_network_groups))

        if len(sandboxes) < num_network_groups :
            message = ("Number of sandbox %d is less than number of network groups %d")
            raise exceptions.InvalidConfigException(
                message  % (len(sandboxes), num_network_groups))
        elif (len(sandboxes) % num_network_groups) != 0 :
            message = ("Number of sandbox %d is not divisible by network groups %d")
            raise exceptions.InvalidConfigException(
                message  % (len(sandboxes), num_network_groups))


        group_spread_sandboxes = len(sandboxes) / num_network_groups
        LOG.info("Number of group spread sandboxes: %s" % str(group_spread_sandboxes))

        network_groups = []
        networks_per_group = num_networks / num_network_groups
        base = 0
        for i in range(0, num_network_groups):
            LOG.info("Group %d" % i)
            network_group = []

            for j in range(base, base + networks_per_group):
                network_group.append(logical_networks[j])
                LOG.info("\t%d, add logical network: %s" % (j, logical_networks[j].get_lswitch()))

            LOG.info("network group idx0: %s" % network_group[0].get_lswitch())

            network_groups.append(network_group)
            base += networks_per_group

        LOG.info("Allocating sandboxes...")
        sandbox_idx = 0
        base = 0
        for group in network_groups:
            for network in group:
                LOG.info("network switch name: %s" % network.get_lswitch())
                for sandbox_idx in range(base, base + group_spread_sandboxes):
                    network.add_sandbox(sandboxes[sandbox_idx])
                    LOG.info("\tAdd sandbox %s" % sandboxes[sandbox_idx])
            base += group_spread_sandboxes

        LOG.info("Network groups %s" % network_groups)

    return logical_networks

class OvnNetwork(ovn.OvnScenario):
    """scenarios for OVN network."""


    @scenario.configure(context={})
    def create_networks(self, network_create_args):
        self._create_networks(network_create_args)


    def connect_networks_to_routers(self, lnetworks, lrouters, networks_per_router):
        j = 0
        for i in range(len(lrouters)):
            lrouter = lrouters[i]
            LOG.info("Connect %s networks to router %s" % (networks_per_router, lrouter["name"]))
            for k in range(j, j+int(networks_per_router)):
                lnetwork = lnetworks[k]
                LOG.info("connect networks %s cidr %s" % (lnetwork["name"], lnetwork["cidr"]))
                self._connect_network_to_router(lrouter, lnetwork)

            j += int(networks_per_router)

    @scenario.configure(context={})
    def create_routers(self, router_create_args=None,
                       router_connection_method=None,
                       networks_per_router=None,
                       network_create_args=None):
        lrouters = self._create_routers(router_create_args)

        num_router = int(router_create_args.get("amount", 0))
        num_networks = int(networks_per_router) * num_router
        lnetworks = self._create_networks(network_create_args, num_networks)

        for i in range(len(lnetworks)):
            lnetwork = lnetworks[i]
            LOG.info("networks %s cidr %s" % (lnetwork["name"], lnetwork["cidr"]))

        self.connect_networks_to_routers(lnetworks, lrouters, networks_per_router)


    @validation.number("ports_per_network", minval=1, integer_only=True)
    @scenario.configure(context={})
    def create_routers_bind_ports(self, router_create_args=None,
                                  router_connection_method=None,
                                  networks_per_router=None,
                                  network_create_args=None,
                                  chassis_per_network=None,
                                  port_create_args=None,
                                  ports_per_network=None,
                                  port_bind_args=None):

        # Create routers and logical networks, and connect them
        lrouters = self._create_routers(router_create_args)

        num_router = int(router_create_args.get("amount", 0))
        num_networks = int(networks_per_router) * num_router
        lnetworks = self._create_networks(network_create_args, num_networks)

        for i in range(len(lnetworks)):
            lnetwork = lnetworks[i]
            LOG.info("networks %s cidr %s" % (lnetwork["name"], lnetwork["cidr"]))

        self.connect_networks_to_routers(lnetworks, lrouters, networks_per_router)

        # Create ports on the logical networks
        sandboxes = self.context["sandboxes"]

        logical_networks = []
        logical_networks = initialize_logical_networks(lnetworks)
        if chassis_per_network == None:
            chassis_per_network = len(sandboxes)
        logical_networks = allocate_networks_on_sandboxes_v2(logical_networks, sandboxes, chassis_per_network)

        LOG.info("Logical networks %s" % logical_networks[0].get_lswitch())
        LOG.info("Allocate network successfully")
        # return

        for logical_network in logical_networks:
            lports = self._create_lports(logical_network.get_lswitch(), port_create_args, ports_per_network)
            if (len(lports) < len(logical_network.get_sandboxes())):
                LOG.warn("Number of ports less than chassis: inbalance binding\n")
            self._bind_ports(lports, logical_network.get_sandboxes(), port_bind_args)
            # self._of_check_ports(lports, sandboxes, port_bind_args)



    @validation.number("ports_per_network", minval=1, integer_only=True)
    @scenario.configure(context={})
    def create_and_bind_ports(self,
                              network_create_args=None,
                              networks_per_sandbox=None,
                              chassis_per_network=None,
                              port_create_args=None,
                              ports_per_network=None,
                              port_bind_args=None):

        sandboxes = self.context["sandboxes"]

        lswitches = self._create_networks(network_create_args)

        logical_networks = []
        logical_networks = initialize_logical_networks(lswitches)
        if networks_per_sandbox == None:
            networks_per_sandbox = 0
        # logical_networks = allocate_networks_on_sandboxes(logical_networks, sandboxes, networks_per_sandbox)
        logical_networks = allocate_networks_on_sandboxes_v2(logical_networks, sandboxes, chassis_per_network)

        LOG.info("Logical networks %s" % logical_networks[0].get_lswitch())
        LOG.info("Allocate network successfully")
        # return

        for logical_network in logical_networks:
            lports = self._create_lports(logical_network.get_lswitch(), port_create_args, ports_per_network)
            if (len(lports) < len(logical_network.get_sandboxes())):
                LOG.warn("Number of ports less than chassis: inbalance binding\n")
            self._bind_ports(lports, logical_network.get_sandboxes(), port_bind_args)
            # self._of_check_ports(lports, sandboxes, port_bind_args)

    @validation.number("switch_name", integer_only=False)
    @scenario.configure(context={})
    def add_ports_to_network(self,
                            network_args=None,
                            port_create_args=None,
                            ports_per_network=None,
                            port_bind_args=None):

        sandboxes = self.context["sandboxes"]

        lswitch = {"name": ""}
        lswitch["name"] = network_args.get("lswitch_name", "None")

        LOG.info("Add ports to swtich %s" % lswitch)

        #for lswitch in lswitches:
        lports = self._create_lports(lswitch, port_create_args, ports_per_network)
        self._bind_ports(lports, sandboxes, port_bind_args)
        #    self._of_check_ports(lports, sandboxes, port_bind_args)

    def bind_ports(self):
        pass

    def bind_and_unbind_ports(self):
        pass


