Benchmarking Suricata in Different Isolation Systems Using TCPreplay
====================================================================

## Introduction

Containers like LXC are becoming a popular solution to program isolation. Compared to virtual machines, containers tend to have less
resource overhead and higher performance. In this experiment we explore how much sense it will make moving 
[Suricata](http://suricata-ids.org/), a popular multi-threaded IDS program, from a virtual machine to a container. We compare
performance and resource usage of Suricata in bare metal, Docker container, and virtual machine setups, and in different load levels
and resource allocation configurations.

## Method

Use [tcpreplay](http://tcpreplay.appneta.com/) to replay some Pcap traffic files collected from the Internet, and analyze performance
of Suricata (running in bare metal, Docker, and VM, respectively) from statistics it reports and resource usage of related processes
and resource availability of the entire host.

When comparing Docker container and VM, we will also tune the resource limit and see how Suricata will perform.

### Hardware

We use four servers of the same hardware configuration. They form two pairs of test setups -- (cap03, cap09) and (cap06, cap07). cap03
and cap06 are hosts to run Suricata, while cap09 and cap07 are hosts to run tcpreplay (which is CPU intensive) and control script.
The two hosts of each pair are connected directly by an Ethernet cable.

All four machines have the following hardware configuration:

 * CPU: [Intel Xeon X3430 @ 2.40GHz](http://ark.intel.com/products/42927/Intel-Xeon-Processor-X3430-8M-Cache-2_40-GHz) (Nehalem; [EIST](https://en.wikipedia.org/wiki/SpeedStep)/C-states disabled; VT-x on, VT-d on; HT unsupported)
 * RAM: 2 x 2 GB DDR3-1333 RAM
 * HDD: 500GB Seagate 3.5" 7200RPM + 2 x 1TB Seagate 3.5" 7200RPM
 * Network: 2 x Broadcom 1Gbps NIC. **em1** (**enp32s0** on cap03/cap06) is used for remote access and management, and **em2**
 (**enp34s0** on cap03/cap06) is used to transmit the test traffic.

### Software

#### Sender Host (cap07/cap09)

Senders run Ubuntu Server 14.04.4 64-bit.

|  Package name  | Version |
|:--------------:|:-------:|
| gcc            | 4.8.4   |
| tcpreplay      | 4.1.1   |
| python3        | 3.4     |
| python3-spur   | 0.3.16  |
| python3-psutil | 4.1.0   |

#### Receiver Host (cap03/cap06)

Receivers run Ubuntu Server 15.10 64-bit. The reason is that many packages (particularly QEMU, which dates 8 years ago) on Ubuntu
14.04 are too old; some (libvirt 1.2.2) are even buggy.

|     Package      |    Host    |   Docker  |     VM      |
|:----------------:|:----------:|:---------:|:-----------:|
|     Docker       |   1.11.0   |     -     |    -        |
|     libvirt      |   1.3.3    |     -     |    -        |
|     gcc          |   5.2.1    |   5.2.1   |   5.2.1     |
|     Suricata     |    3.0.1   |   3.0.1   |    3.0.1    |
|  Emerging Rules  |   20160414 |  20160414 |   20160414  |
|  python3         |   3.4      |    -      |   3.4       |
|  python3-spur    |    0.3.16  |    -      |     -       |
|  python3-psutil  |  4.1.0     |    -      |     4.1.0   |

The VM resembles software of host system, running Ubuntu Server 15.10 64-bit and making sure all critical packages are of the same version as the host.

##### Side notes

 * To use streamlined test script, host user and sender must be able to run sudo without password prompt
   (`sudo visudo` and add `username ALL=(ALL) NOPASSWD: ALL`).
 * Use SSH authorized_keys to facilitate SSH login.

#### Suricata

Suricata loads the free version of [Emerging Rules](http://rules.emergingthreats.net/open/suricata/) as of 2016-04-14.

Unless otherwise noted, Suricata uses default configuration generated when installed to the system.

Suricata 3.0.1, released on April 4, 2016, [fixed many memory leak bugs and improved stability](http://suricata-ids.org/news/).
This can be confirmed by our previous testing of 3.0 version inside VM setup, which resulted in memory thrashing and can barely
be tested in any load above moderate.

#### Trace files

We use the following flows available from the Internet:

 * [Sample flows provided by TCPreplay](http://tcpreplay.appneta.com/wiki/captures.html) -- `bigFlows.pcap` (359,457 KB), `smallFlows.pcap` (9,224 KB).
 * [Sample traces collected by WireShark](https://wiki.wireshark.org/SampleCaptures)
 * [Publicly available PCAP files](http://www.netresec.com/?page=PcapFiles)
 * [ISTS'12 trace files](http://www.netresec.com/?page=ISTS) -- randomly picked `snort.log.1425823194` (155,823 KB).

##### bigFlows.pcap

According to TCPreplay website, bigFlows.pcap has the following characteristics:

 > This is a capture of real network traffic on a busy private network's access point to the Internet. The capture is much larger and
 > has a smaller average packet size than the previous capture. It also has many more flows and different applications. If the large
 > size of this file isn't a problem, you may want to select it for your tests.
 > 
 > * Size: 368 MB
 > * Packets: 791615
 > * Flows: 40686
 > * Average packet size: 449 bytes
 > * Duration: 5 minutes
 > * Number Applications: 132

From the log of Suricata we can confirm that the traffic consists of numerous procotols on various ISO/OSI layers.

The peak throughput of the trace is approximately 2.13 MBps (diagram will given later), so our Ethernet link will support about 50 parallel TCPreplay processes.

#### Performance Analysis

We analyze the performance of Suricata by comparing speed of packets / bytes captured, speed of packets / bytes decoded, and
speed of alerts triggered for different setups when playing the same trace with the same number of parallel workers. Theoretically the
speed of traffic sent is the same, so the difference of those speeds result from the receiver setup.

Suricata generates stats every 8 seconds (default value).

#### Resource Monitoring

We use a Python script based on Python3 `psutil` package. It periodically polls the system-wide CPU, memory, and Disk I/O usage, and
optionally the traffic sent / received on specified NIC, and sum of resource usage of a subset of processes (e.g., `docker` processes
and their children processes) and outputs the information to a CSV file. We compared the numbers with popular system monitor programs
like `top`, `htop`, `atop` (buggy, discussed later) and can confirm that the numbers are correct and the periods between polls are
(almost perfectly) constant.

Resource monitor polls stats every 4 seconds.

The source code of resource monitor is hosted in [`tester_script/`](tester_script/) directory.

___Why not use `top` or `atop` directly?___

 - Because `top` and `atop` polls more numbers than needed, they incur much higher overhead on the receiver system.
 - Output is not friendly for post-processing, even after CSV-fied.
 - Lines of `top` do not contain timestamps; because we start monitors before Suricata, we cannot ask monitors to poll information 
   of Suricata process (its PID not known beforehand).
 - `atop` behaves wrong on our system. When running VM setup, `atop` reports 50% of CPU usage each core while in fact they are all
   100% (confirmed by `htop` and `top`).
 - Because `atop` and `top` (which needs to monitor several processes like two `docker` processes and one `Suricata-Main` process)
   are separate processes, their output seldom hits the same timestamp, and thus the sum of the reported numbers is not accurate.

By contrast, our monitor script prints neatly for each polling timestamp all the system-wide resource availability and sum of resource
usage of the processes we are interested in one CSV line. This makes post-processing easy as well.

___Why examine system-wide resource usage?___

Because the sum of resource usage of processes that are directly related may not be comprehensive. For example, the RAM usage of mirroring traffic to macvtap is not in any suricata, docker, or qemu processes.

System-wide numbers could over-count, but as we are comparing the difference, which results from different setups of Suricata, the over-counted part doesn't matter.

### Test Setups

#### Bare metal

In bare metal setting, Suricata will run directly on top of hardware and inspect the NIC that the test traffic enters.

![Bare metal setup](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/diagrams/bare_metal.svg)

#### Docker

In this Docker setting, the container is configured so that the network interfaces of the host is exposed to the container, enabling
Suricata to inspect the same NIC interface as in bare metal setting.

The CPU and RAM limitations can be passed as parameters of the test script. By default, it allows the container to access all 4 cores
and has a RAM limit of 2GB (1536m and 1g are also tested).

![Docker setup](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/diagrams/docker.svg)

#### Docker + macvtap

In Docker-vtap setting, the difference from Docker setup is that we create a macvtap of model "virtio" and mode "passthrough" to
mirror the traffic arriving at host's enp34s0 NIC, and let Suricata in Docker inspect the traffic on the macvtap device. This is an "intermediate" setup between Docker setup and VM setup, because the cost of running macvtap is unavoidable in VM setup.

![Docker-vtap setup](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/diagrams/docker_vtap.svg)

#### Virtual machine

The virtual machine hardware is configurable. Default configurations are available in XML format in
[`config/`](config/). Different CPU and RAM configuration may be passed as parameters of the test script.
By default, it has 4 vCPUs each of which has access to all 4 cores of the host CPU. Capacities of vCPU are copied from host CPU
("host-model"). RAM is set to 2 GB. In terms of NIC, We create a macvtap device (macvtap0) of model "virtio" and mode "passthrough" to
copy the test traffic arriving at host's enp34s0 to VM's eth1. Another NIC, eth0, is added for communications between host and the VM.

The exact hardware configuration will be mentioned when comparing results.

The virtual disk has size of 64 GiB, large enough to hold logs of GB magnitude.

![Virtual machine setup](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/diagrams/vm.svg)

### Test cases

We have the following tests:

|     Setup     | Trace file    | Para. TCPreplays | Use VTAP? |  Memory  | CPU | Swappiness | Other Args              | Sample Size |
|:-------------:|:-------------:|:----------------:|:---------:|:--------:|:---:|:----------:|:-----------------------:|:-----------:|
|   Bare metal  | bigFlows.pcap |       1          |     No    |   4 GB   |  4  |     5      | -                       |      ?      |
|     Docker    | bigFlows.pcap |       1          |     No    |   2 GB   |  4  |     5      | -                       |      ?      |
| Docker + vtap | bigFlows.pcap |       1          |    Yes    |   2 GB   |  4  |     5      | -                       |      ?      |
|       VM      | bigFlows.pcap |       1          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4                 |      ?      |
|   Bare metal  | bigFlows.pcap |       2          |     No    |   4 GB   |  4  |     5      | -                       |      ?      |
|     Docker    | bigFlows.pcap |       2          |     No    |   2 GB   |  4  |     5      | -                       |      ?      |
| Docker + vtap | bigFlows.pcap |       2          |    Yes    |   2 GB   |  4  |     5      | -                       |      ?      |
|       VM      | bigFlows.pcap |       2          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4                 |      ?      |
|   Bare metal  | bigFlows.pcap |       4          |     No    |   4 GB   |  4  |     5      | -                       |      ?      |
|     Docker    | bigFlows.pcap |       4          |     No    |   2 GB   |  4  |     5      | -                       |      ?      |
| Docker + vtap | bigFlows.pcap |       4          |    Yes    |   2 GB   |  4  |     5      | -                       |      ?      |
|       VM      | bigFlows.pcap |       4          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4                 |      ?      |
|   Bare metal  | bigFlows.pcap |       8          |     No    |   4 GB   |  4  |     5      | -                       |      ?      |
|     Docker    | bigFlows.pcap |       8          |     No    |   2 GB   |  4  |     5      | -                       |      ?      |
| Docker + vtap | bigFlows.pcap |       8          |    Yes    |   2 GB   |  4  |     5      | -                       |      ?      |
|       VM      | bigFlows.pcap |       8          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4                 |      ?      |
|     Docker    | bigFlows.pcap |       4          |     No    | 1536 MB  |  4  |     5      | -                       |      ?      |
| Docker + vtap | bigFlows.pcap |       4          |    Yes    | 1536 MB  |  4  |     5      | -                       |      ?      |
|       VM      | bigFlows.pcap |       4          |    Yes    | 1536 MB  |  4  |     5      | vCPUs=4                 |      ?      |
|     Docker    | bigFlows.pcap |       4          |     No    | 1024 MB  |  4  |     5      | -                       |      ?      |
| Docker + vtap | bigFlows.pcap |       4          |    Yes    | 1024 MB  |  4  |     5      | -                       |      ?      |
|       VM      | bigFlows.pcap |       4          |    Yes    | 1024 MB  |  4  |     5      | vCPUs=4                 |      ?      |
|     Docker    | bigFlows.pcap |       16         |     No    |   2 GB   |  4  |     5      | -                       |   Planned   |
| Docker + vtap | bigFlows.pcap |       16         |    Yes    |   2 GB   |  4  |     5      | -                       |   Planned   |
|     Docker    | bigFlows.pcap |       32         |     No    |   2 GB   |  4  |     5      | -                       |   Planned   |
| Docker + vtap | bigFlows.pcap |       32         |    Yes    |   2 GB   |  4  |     5      | -                       |   Planned   |

We ran each test multiple times to generate a number of instances (as the sample size column above reflects), and use the median of all
instances at each stat point to obtain an average result of the test. We then compare the average result of each tests.

The script to parse raw CSV / Suricata eve.json files is hosted in [`dataparser/`](dataparser/) directory.

## Result

