#!/bin/bash

# This script is to solve the problem "libGL.so not found." on Ubuntu Server 15.10.
# when running virt-manager.
# Source: http://askubuntu.com/questions/745422/usr-bin-ld-cannot-find-lgl

sudo apt-get purge "fglrx.*"
sudo rm /etc/X11/xorg.conf
sudo apt-get install --reinstall xserver-xorg-core libgl1-mesa-glx libgl1-mesa-dri
sudo dpkg-reconfigure xserver-xorg-core

# sudo reboot
