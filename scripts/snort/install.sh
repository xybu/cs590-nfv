#!/bin/bash

# According to
# https://www.snort.org/documents/snort-2-9-8-x-on-ubuntu-12-lts-and-14-lts-and-15

TMPDIR="/tmp"
SNORT_VER="2.9.8.3"

sudo apt-get install -yq wget libpcre3-dev libpcap-dev libdumbnet-dev \
	build-essential make autoconf automake libtool flex bison \
	zlib1g-dev liblzma-dev openssl libssl-dev libnetfilter-queue-dev \
    iptables-dev

cd $TMPDIR
wget https://www.snort.org/downloads/snort/daq-2.0.6.tar.gz
tar xvf daq-2.0.6.tar.gz
wget https://www.snort.org/downloads/snort/snort-$SNORT_VER.tar.gz
tar xvf snort-$SNORT_VER.tar.gz
wget http://rules.emergingthreats.net/open/snort-edge/emerging.rules.tar.gz
tar xvf emerging.rules.tar.gz

cd $TMPDIR/daq-2.0.6
./configure
make
sudo make install
sudo ldconfig

cd $TMPDIR/snort-$SNORT_VER
./configure --enable-sourcefire --enable-perfprofiling
make -j2
sudo make install
sudo ldconfig

sudo chmod u+s /usr/local/bin/snort
sudo ln -s /usr/local/bin/snort /usr/sbin/snort

# Create the Snort directories.
sudo mkdir /etc/snort
sudo mkdir /etc/snort/rules
sudo mkdir /etc/snort/rules/iplists
sudo mkdir /etc/snort/preproc_rules
sudo mkdir /usr/local/lib/snort_dynamicrules
sudo mkdir /etc/snort/so_rules

# Create some files that stores rules and ip lists
sudo touch /etc/snort/rules/iplists/black_list.rules
sudo touch /etc/snort/rules/iplists/white_list.rules
sudo touch /etc/snort/rules/local.rules
sudo touch /etc/snort/sid-msg.map

# Create our logging directories.
sudo mkdir /var/log/snort
sudo mkdir /var/log/snort/archived_logs

# Adjust permissions.
sudo chmod -R 5775 /var/log/snort
sudo chmod -R 5775 /var/log/snort/archived_logs
sudo chmod -R 5775 /etc/snort
sudo chmod -R 5775 /etc/snort/rules
sudo chmod -R 5775 /etc/snort/so_rules
sudo chmod -R 5775 /etc/snort/preproc_rules
sudo chmod -R 5775 /usr/local/lib/snort_dynamicrules

# Copy rules and conf from source tarball
cd $TMPDIR/snort-$SNORT_VER/etc/
sed -i -e "s/var RULE_PATH ..\/rules/var RULE_PATH \/etc\/snort\/rules/" \
		-e "s/var SO_RULE_PATH ..\/so_rules/var SO_RULE_PATH \/etc\/snort\/so_rules/"  \
		-e "s/var PREPROC_RULE_PATH ..\/preproc_rules/var PREPROC_RULE_PATH \/etc\/snort\/preproc_rules/"  \
		-e "s/var WHITE_LIST_PATH ..\/rules/var WHITE_LIST_PATH \/etc\/snort\/rules\/iplists/"  \
		-e "s/var BLACK_LIST_PATH ..\/rules/var BLACK_LIST_PATH \/etc\/snort\/rules\/iplists/"  \
		-e "s/include \$RULE\_PATH/#include \$RULE\_PATH/" \
		-e "s/include classification.config/#include classification.config/" \
		-e "s/include reference.config/#include reference.config/" snort.conf
echo "include \$RULE_PATH/emerging.conf" >> ./snort.conf
sudo cp *.conf* /etc/snort
sudo cp *.map /etc/snort
sudo cp *.dtd /etc/snort

cd $TMPDIR/snort-$SNORT_VER/src/dynamic-preprocessors/build/usr/local/lib/snort_dynamicpreprocessor/
sudo cp * /usr/local/lib/snort_dynamicpreprocessor/

# Install Emerging Rules

cd $TMPDIR/rules
sed -i -e "s/#include \$RULE\_PATH/include \$RULE\_PATH/" \
		-e "s/include \$RULE_PATH\/.*-BLOCK\.rules//" emerging.conf
find . -name "*.rules" -type f -exec sed -i -e 's/\!\[\$SMTP_SERVERS,\$DNS_SERVERS\]/any/g' \
 -e 's/\!\[\$DNS_SERVERS,\$SMTP_SERVERS\]/any/g' \
 -e 's/\!\$SMTP_SERVERS/any/g' \
 -e 's/\!\$DNS_SERVERS/any/g' \
 -e 's/\!\$HOME_NET/any/g' {} \;
sudo mv * /etc/snort/rules/

sudo rm -rfv $TMPDIR/*.gz $TMPDIR/daq-2.0.6 $TMPDIR/snort-$SNORT_VER $TMPDIR/rules
