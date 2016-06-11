#!/bin/bash

echo "Test ovn-scale-test containerized deployment"

uname -a
ifconfig
ansible-playbook --version

# Create Ansible inventory file
mkdir -p /etc/ansible
ls /etc/ansible
printf "[ovn-database]\n127.0.0.1\n" > /etc/ansible/hosts
printf "[emulation-hosts]\n127.0.0.1 provider_ip=127.0.0.1\n" >> /etc/ansible/hosts
printf "[rally]\n127.0.0.1\n" >> /etc/ansible/hosts
cat /etc/ansible/hosts
