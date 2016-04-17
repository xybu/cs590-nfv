#!/bin/bash

# This script is to configure a newly installed Ubuntu Server 15.10.

sudo apt-get update && sudo apt-get upgrade
sudo apt-get -y install ack-grep build-essential cmake automake gcc g++ valgrind curl vim-tiny \
	gawk ssh libcurl4-openssl-dev openssl python-software-properties software-properties-common \
	python3-dev python-dev git mercurial

alias vi=vim

# No sudo password prompt. Should change username.
sudo bash -c 'echo -e "\nbu1 ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers'

# Configure Mercurial.
echo "[ui]" > ~/.hgrc
echo "username = Xiangyu Bu <xybu92@live.com>" >> ~/.hgrc
echo "verbose = True" >> ~/.hgrc

# Configure VIM.
echo "colorscheme elflord" >> ~/.vimrc

# Configure Git.
git config --global user.name "Xiangyu Bu"
git config --global user.email "xybu92@live.com"
git config --global core.editor vim

# Copy ssh key.
rsync -zrvpE bu1@cap08:/home/bu1/.ssh ~/
sudo mkdir -p /root/.ssh
sudo cp /home/bu1/.ssh/* /root/.ssh/

# Mount extra hard disks.
sudo bash -c 'echo -e "/dev/sdb1\t/scratch\t\t\t\text4\tnodev,nosuid,acl\t\t1\t\t2" >> /etc/fstab'
sudo bash -c 'echo -e "/dev/sdc1\t/scratch2\t\t\t\text4\tnodev,nosuid,acl\t\t1\t\t2" >> /etc/fstab'

# Configure swappiness.
sudo bash -c 'echo -e "vm.swappiness = 5" >> /etc/sysctl.conf'

# Configure em2.
sudo bash -c 'echo "" >> /etc/network/interfaces'
sudo bash -c 'echo "auto em2" >> /etc/network/interfaces'
sudo bash -c 'echo "iface em2 inet static" >> /etc/network/interfaces'
sudo bash -c 'echo "address 192.168.0.1" >> /etc/network/interfaces'
sudo bash -c 'echo "network 192.168.0.0" >> /etc/network/interfaces'
sudo bash -c 'echo "netmask 255.255.255.0" >> /etc/network/interfaces'
sudo bash -c 'echo "broadcast 192.168.0.255" >> /etc/network/interfaces'

# Install docker.
curl -fsSL https://get.docker.com/gpg | sudo apt-key add -
curl -fsSL https://get.docker.com/ | sh
sudo usermod -aG docker $USER

# Fix cgroup issue.
sed "s/GRUB_TIMEOUT=[0-9]*/GRUB_TIMEOUT=0/" /etc/default/grub | tee /tmp/grub
sed "s/GRUB_CMDLINE_LINUX=\"\"/GRUB_CMDLINE_LINUX=\"cgroup_enable=memory swapaccount=1\"/" /tmp/grub | sudo tee /etc/default/grub
sudo update-grub

# Install QEMU/KVM.
./qemu/install.sh

# Install Suricata
./suricata/install.sh

# Configure Python.
wget -O- https://bootstrap.pypa.io/get-pip.py | sudo python3
sudo pip install -U psutil
sudo pip install -U docker-py
sudo pip install -U spur
