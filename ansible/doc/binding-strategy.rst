======================
Binding Strategy Guide
======================

Overview
========

In OVN, a logical port can be bind to a local OVS port on any
chassis/hypervisor, depending on the VM scheduler (e.g., ``nova-scheduler``).
The binding strategy potentially impacts the network performance. That is
binding all logical ports from a logical network on a single hypervisor performs
differently than distributing the ports on multiple hypervisors.

The container-based ovn-scale-test deployment allows to configure the binding
strategy in creating and binding port rally task.


Binding Configuration
=====================

Use ``chassis_per_network`` to control how logical networks and the logical
ports are bind to chassis.

For example, given ``ovn_number_chassis: 10`` (10 emulated chassis) and
``network_number: 5`` (5 logical networks), the binding varies depending
on the value of ``chassis_per_network``.

- ``chassis_per_network: "10"``: this is the default case. Each network spans on
the 10 chassis


- ``chassis_per_network: "2"``: each network will allocate its ports to two
chassis. In the rally_ovs implementation, we randomly select two chassis out of
the 10 chassis. Although some randomness, the overall allocation follows a
uniform distribution.


- ``chassis_per_network: "1"``: each network allocates all its port to a single
chassis. Note that this is the extreme case as opposite to
``chassis_per_network: "10"``.


Constraint
~~~~~~~~~

``chassis_per_network`` must be [1, ``num_chassis``].


Implementation Detail
=====================

TBD
