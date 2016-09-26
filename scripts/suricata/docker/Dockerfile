# Use latest ubuntu LTS
FROM ubuntu:xenial

# ENV VIRTUSER user
# Suricata version.
ENV VER=3.1.2
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies.
# https://redmine.openinfosecfoundation.org/projects/suricata/wiki/Ubuntu_Installation
RUN apt-get update -qq
RUN apt-get upgrade -yq
RUN apt-get install -yq wget
RUN apt-get install -yq libpcre3 libpcre3-dbg libpcre3-dev \
build-essential make autoconf automake libtool libpcap-dev libnet1-dev \
libyaml-0-2 libyaml-dev zlib1g zlib1g-dev libmagic-dev libcap-ng-dev \
libjansson-dev pkg-config libgeoip-dev libnetfilter-queue-dev \
libnetfilter-queue-dev libnetfilter-queue1 libnfnetlink-dev libnfnetlink0

# Install Sucicata.
# USER $VIRTUSER
WORKDIR /tmp
RUN wget http://www.openinfosecfoundation.org/download/suricata-$VER.tar.gz
RUN tar -xvzf suricata-$VER.tar.gz
WORKDIR /tmp/suricata-$VER
RUN ./configure --enable-nfqueue --enable-unittests --enable-profiling --prefix=/usr --sysconfdir=/etc --localstatedir=/var
RUN make -j2
# USER root
RUN make install-full
RUN ldconfig
RUN mkdir -p /var/log/suricata

RUN chmod u+s /usr/bin/suricata
