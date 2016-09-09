#!/bin/bash

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace
set -o errexit

# Configurable variables
# num_chassis=40
rally_image="huikang/ovn-scale-test-rally-upstream-test"

# for num_chassis in 60 80 100
for num_chassis in 200 400 600
do
for num_network_sandbox in 10 50 100 500 1000
# for num_network_sandbox in 10 
do
    # num_networks=$(( $num_chassis * $num_network_sandbox ))
    num_networks=2000
    file_name="./ci/rally_ovs_${num_chassis}_chassis_${num_network_sandbox}_net-sandbox_${num_networks}_networks"
    echo "Running create_and_binding ${num_chassis} sandboxes; ${num_networks} networks; ${num_network_sandbox} network/sandbox" >> ${file_name}

    # Deploy sandboxes
    ansible-playbook -i ansible/inventory/rdu39-hosts ansible/site.yml -e @ansible/etc/rdu39-variables.yml \
	-e rally_image=${rally_image} \
	-e ovn_number_chassis=${num_chassis} \
	-e networks_per_sandbox=${num_network_sandbox} \
	-e network_number=${num_networks} \
	-e action=deploy

    # Registerring rally environment
    docker exec ovn-rally rally-ovs deployment create --file /root/rally-ovn/ovn-multihost-deployment.json --name ovn-multihost
    docker exec ovn-rally rally-ovs task start /root/rally-ovn/workload/create-sandbox-x240r3n24.json
    docker exec ovn-rally rally-ovs task start /root/rally-ovn/workload/create-sandbox-x240gr2n11.json
    
    # Run rally_ovs workload; output to file
    echo "Start run rally_ovs workload"
    sleep 10
    docker exec ovn-rally rally-ovs task start /root/rally-ovn/workload/create_and_bind_ports.json >> ${file_name}

    # Cleanup deployment
    ansible-playbook  -i ansible/inventory/rdu39-hosts ansible/site.yml -e @ansible/etc/rdu39-variables.yml -e ovn_number_chassis=${num_chassis} -e rally_image=huikang/ovn-scale-test-rally-upstream-test -e action=clean

    # break
    sleep 20
done
done

# Restore xtrace
$XTRACE
