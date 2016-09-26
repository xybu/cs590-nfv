FROM ubuntu:xenial

ENV TMPDIR=/tmp
ENV SNORT_VERSION=2.9.8.3
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq
RUN apt-get upgrade -yq
RUN apt-get install -yq wget sed
RUN apt-get install -yq wget libpcre3-dev libpcap-dev libdumbnet-dev \
	build-essential make autoconf automake libtool flex bison \
	zlib1g-dev liblzma-dev openssl libssl-dev libnetfilter-queue-dev \
    iptables-dev

WORKDIR $TMPDIR
RUN wget https://www.snort.org/downloads/snort/daq-2.0.6.tar.gz
RUN tar xvf daq-2.0.6.tar.gz
RUN wget https://www.snort.org/downloads/snort/snort-$SNORT_VERSION.tar.gz
RUN tar xvf snort-$SNORT_VERSION.tar.gz
RUN wget http://rules.emergingthreats.net/open/snort-edge/emerging.rules.tar.gz
RUN tar xvf emerging.rules.tar.gz

WORKDIR $TMPDIR/daq-2.0.6
RUN ./configure
RUN make -j2
RUN make install
RUN ldconfig

WORKDIR $TMPDIR/snort-$SNORT_VERSION
RUN ./configure --enable-sourcefire --enable-perfprofiling
RUN make
RUN make install
RUN ldconfig

RUN chmod u+s /usr/local/bin/snort
RUN ln -s /usr/local/bin/snort /usr/sbin/snort

# Create the Snort directories.
RUN mkdir /etc/snort
RUN mkdir /etc/snort/rules
RUN mkdir /etc/snort/rules/iplists
RUN mkdir /etc/snort/preproc_rules
RUN mkdir /usr/local/lib/snort_dynamicrules
RUN mkdir /etc/snort/so_rules

# Create some files that stores rules and ip lists
RUN touch /etc/snort/rules/iplists/black_list.rules
RUN touch /etc/snort/rules/iplists/white_list.rules
RUN touch /etc/snort/rules/local.rules
RUN touch /etc/snort/sid-msg.map

# Create our logging directories.
RUN mkdir /var/log/snort
RUN mkdir /var/log/snort/archived_logs

# Adjust permissions.
RUN chmod -R 5775 /var/log/snort
RUN chmod -R 5775 /var/log/snort/archived_logs
RUN chmod -R 5775 /etc/snort
RUN chmod -R 5775 /etc/snort/rules
RUN chmod -R 5775 /etc/snort/so_rules
RUN chmod -R 5775 /etc/snort/preproc_rules
RUN chmod -R 5775 /usr/local/lib/snort_dynamicrules

# Copy rules and conf from source tarball
WORKDIR $TMPDIR/snort-$SNORT_VERSION/etc/
RUN sed -i "s/var RULE_PATH ..\/rules/var RULE_PATH \/etc\/snort\/rules/" snort.conf
RUN sed -i "s/var SO_RULE_PATH ..\/so_rules/var SO_RULE_PATH \/etc\/snort\/so_rules/" snort.conf
RUN sed -i "s/var PREPROC_RULE_PATH ..\/preproc_rules/var PREPROC_RULE_PATH \/etc\/snort\/preproc_rules/" snort.conf
RUN sed -i "s/var WHITE_LIST_PATH ..\/rules/var WHITE_LIST_PATH \/etc\/snort\/rules\/iplists/" snort.conf
RUN sed -i "s/var BLACK_LIST_PATH ..\/rules/var BLACK_LIST_PATH \/etc\/snort\/rules\/iplists/" snort.conf
RUN sed -i "s/include \$RULE\_PATH/#include \$RULE\_PATH/" snort.conf
RUN sed -i "s/include classification.config/#include classification.config/" snort.conf
RUN sed -i "s/include reference.config/#include reference.config/" snort.conf
RUN echo "include \$RULE_PATH/emerging.conf" >> $TMPDIR/snort-$SNORT_VERSION/etc/snort.conf
RUN cp *.conf* /etc/snort
RUN cp *.map /etc/snort
RUN cp *.dtd /etc/snort

WORKDIR $TMPDIR/snort-$SNORT_VERSION/src/dynamic-preprocessors/build/usr/local/lib/snort_dynamicpreprocessor/
RUN cp * /usr/local/lib/snort_dynamicpreprocessor/

# Install Emerging Rules
WORKDIR $TMPDIR/rules
RUN sed -i "s/#include \$RULE\_PATH/include \$RULE\_PATH/" emerging.conf
RUN sed -i "s/include \$RULE_PATH\/.*-BLOCK\.rules//" emerging.conf
RUN find . -name "*.rules" -type f -exec sed -i -e 's/\!\[\$SMTP_SERVERS,\$DNS_SERVERS\]/any/g' \
 -e 's/\!\[\$DNS_SERVERS,\$SMTP_SERVERS\]/any/g' \
 -e 's/\!\$SMTP_SERVERS/any/g' \
 -e 's/\!\$DNS_SERVERS/any/g' \
 -e 's/\!\$HOME_NET/any/g' {} \;
# RUN find . -name "*.rules" -type f -exec sed -i 's/\!\[\$SMTP_SERVERS,\$DNS_SERVERS\]/any/g' {} \;
# RUN find . -name "*.rules" -type f -exec sed -i 's/\!\[\$DNS_SERVERS,\$SMTP_SERVERS\]/any/g' {} \;
# RUN find . -name "*.rules" -type f -exec sed -i 's/\!\$SMTP_SERVERS/any/g' {} \;
# RUN find . -name "*.rules" -type f -exec sed -i 's/\!\$DNS_SERVERS/any/g' {} \;
# RUN find . -name "*.rules" -type f -exec sed -i 's/\!\$HOME_NET/any/g' {} \;
RUN mv * /etc/snort/rules/

RUN rm -rf $TMPDIR/*.gz $TMPDIR/daq-2.0.6 $TMPDIR/snort-$SNORT_VERSION $TMPDIR/rules

WORKDIR $TMPDIR
