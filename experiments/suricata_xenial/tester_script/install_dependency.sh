#!/bin/bash

sudo apt-get install python-dev python3-dev
wget -O- https://bootstrap.pypa.io/get-pip.py | sudo python3

# Required for receiver (docker host).
which docker > /dev/null
if [ "$?" -eq "0" ] ; then
	sudo pip install -U docker-py
fi

# Required for both sender and receiver.
sudo pip install -U psutil
sudo pip install -U spur
sudo pip install -U ciso8601
