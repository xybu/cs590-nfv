#!/bin/bash

sudo apt-get install python python-scapy python-feedparser python-cherrypy3
sudo apt-get install nmap hping3 nikto apache2-utils #tcpreplay

sudo apt-get install apache2 vsftpd

cd /tmp
wget http://nmap.org/ncrack/dist/ncrack-0.4ALPHA.tar.gz
tar xvf ncrack-0.4ALPHA.tar.gz
cd ncrack-0.4ALPHA
./configure
make
sudo make install

cd /tmp
wget https://downloads.sourceforge.net/project/pytbull/pytbull-2.1.tar.bz2
tar xvf pytbull-2.1.tar.bz2
sudo mv pytbull /opt/
