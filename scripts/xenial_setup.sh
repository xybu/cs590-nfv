#!/bin/bash

sudo apt-get -y install ack-grep build-essential cmake automake gcc g++ valgrind curl vim-tiny gawk ssh libcurl4-openssl-dev openssl python-software-properties software-properties-common python3-dev python-dev git mercurial

alias vi=vim

echo -e "\nbu1 ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers
echo -e "\nvm.swappiness = 5" | sudo tee -a /etc/sysctl.conf

# Configure Mercurial.
echo "[ui]" > ~/.hgrc
echo "username = Xiangyu Bu <xybu92@live.com>" >> ~/.hgrc
echo "verbose = True" >> ~/.hgrc
echo "editor = vim" >> ~/.hgrc
echo "" >> ~/.hgrc
echo "[extensions]" >> ~/.hgrc
echo "color =" >> ~/.hgrc
echo "purge =" >> ~/.hgrc
echo "histedit =" >> ~/.hgrc

# Configure VIM.
echo "colorscheme elflord" >> ~/.vimrc

# Configure Git.
git config --global user.name "Xiangyu Bu"
git config --global user.email "xybu92@live.com"
git config --global core.editor vim

# Set up SSH keys.
rsync -zrvpE bu1@cap13.cs.purdue.edu:/home/bu1/.ssh /home/bu1/
rsync -zrvpE bu1@cap13.cs.purdue.edu:/home/bu1/.bashrc /home/bu1/
sudo cp -R /home/bu1/.ssh /root/

# Fix cgroup issue.
sed "s/GRUB_TIMEOUT=[0-9]*/GRUB_TIMEOUT=0/" /etc/default/grub | tee /tmp/grub
sed "s/GRUB_CMDLINE_LINUX=\"\"/GRUB_CMDLINE_LINUX=\"cgroup_enable=memory swapaccount=1\"/" /tmp/grub | sudo tee /etc/default/grub
sudo update-grub

# Install Python dependencies.
sudo apt install -y libssl-dev
wget -O- https://bootstrap.pypa.io/get-pip.py | sudo python3
sudo pip install -U psutil
sudo pip install -U spur
sudo pip install -U ciso8601

# Install docker.
curl -fsSL https://get.docker.com/gpg | sudo apt-key add -
curl -fsSL https://get.docker.com/ | sh
sudo usermod -aG docker $USER
sudo pip install -U docker-py

# Mount hard dives.
sudo fsck -p /dev/sdb1 && sudo bash -c 'echo -e "/dev/sdb1\t/scratch\t\t\t\text4\tnodev,nosuid,acl\t\t1\t\t2" >> /etc/fstab'
sudo fsck -p /dev/sdc1 && sudo bash -c 'echo -e "/dev/sdc1\t/scratch2\t\t\t\text4\tnodev,nosuid,acl\t\t1\t\t2" >> /etc/fstab'

# Create user dir.
sudo mkdir /scratch/$USER && sudo chown $USER:$USER /scratch/$USER && ls /scratch -asl
sudo mkdir /scratch2/$USER && sudo chown $USER:$USER /scratch2/$USER && ls /scratch2 -asl

# Configure NIC.
sudo bash -c 'echo "" >> /etc/network/interfaces'
sudo bash -c 'echo "auto enp34s0" >> /etc/network/interfaces'
sudo bash -c 'echo "iface enp34s0 inet static" >> /etc/network/interfaces'
sudo bash -c 'echo -e "\taddress 192.168.0.`tr -cd [:digit:] < /etc/hostname`" >> /etc/network/interfaces'
sudo bash -c 'echo -e "\tnetwork 192.168.0.0" >> /etc/network/interfaces'
sudo bash -c 'echo -e "\tnetmask 255.255.255.0" >> /etc/network/interfaces'
sudo bash -c 'echo -e "\tbroadcast 192.168.0.255" >> /etc/network/interfaces'
sudo ifconfig enp34s0 up
sudo service networking restart
ifconfig
