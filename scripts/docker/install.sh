#!/bin/bash

curl -fsSL https://get.docker.com/gpg | sudo apt-key add -
curl -fsSL https://get.docker.com/ | sh
sudo usermod -aG docker $USER

sudo bash -c 'sed "s/GRUB_CMDLINE_LINUX=\"\"/GRUB_CMDLINE_LINUX=\"cgroup_enable=memory swapaccount=1\"/" /etc/default/grub > /etc/default/grub'
sudo update-grub