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
|     libvirt      |   1.2.16    |     -     |    -        |
|     gcc          |   5.2.1    |   5.2.1   |   5.2.1     |
|     Suricata     |    3.0.1   |   3.0.1   |    3.0.1    |
|  Emerging Rules  |   20160414 |  20160414 |   20160414  |
|  python3         |   3.4      |    -      |   3.4       |
|  python3-spur    |    0.3.16  |    -      |     -       |
|  python3-psutil  |  4.1.0     |    -      |     4.1.0   |

The docker image and VM try to resemble software of host system, running Ubuntu Server 15.10 64-bit and making sure all critical packages are of the same version as the host.

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

The peak throughput of the trace is approximately 2.13 MBps (diagram will given later), so our Ethernet link will support less than 50
concurrent TCPreplay processes. However, CPU of the sender host saturates at 4 concurrent TCPreplay processes; it takes longer for all
TCPreplay processes to finish replaying above that concurrency level (e.g., peak throughput less than doubles at concurrency level 16
compared to concurrency level 4, because at level 16 it can take 3X more time to finish). For this reason, test results above
concurrency level 4 are not comparable to those equal to or below that level. Results not in the same concurrency level above 4 are not
cross-comparable either.

##### snort.log.1425823194

This trace file requires much higher processing speed than `bigFlows.pcap`.

 > * Rated: 6928500.0 Bps, 55.42 Mbps, 6264.04 pps
 > * Flows: 1833 flows, 80.74 fps, 140196 flow packets, 2006 non-flow
 > * Duration: ~22 seconds

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

In the text that follows, I will use "DockerV" to refer to this setup.

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

|     Setup     | Trace file    | Para. TCPreplays | Use VTAP? |  Memory* | CPU | Swappiness | Other Args           | Sample Size |
|:-------------:|:-------------:|:----------------:|:---------:|:--------:|:---:|:----------:|:--------------------:|:-----------:|
|   Bare metal  | bigFlows.pcap |       1          |     No    |   4 GB   |  4  |     5      | -                    |     40      |
|     Docker    | bigFlows.pcap |       1          |     No    |   2 GB   |  4  |     5      | -                    |     40      |
| Docker + vtap | bigFlows.pcap |       1          |    Yes    |   2 GB   |  4  |     5      | -                    |     40      |
|       VM      | bigFlows.pcap |       1          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4              |     40      |
|   Bare metal  | bigFlows.pcap |       2          |     No    |   4 GB   |  4  |     5      | -                    |     40      |
|     Docker    | bigFlows.pcap |       2          |     No    |   2 GB   |  4  |     5      | -                    |     40      |
| Docker + vtap | bigFlows.pcap |       2          |    Yes    |   2 GB   |  4  |     5      | -                    |     40      |
|       VM      | bigFlows.pcap |       2          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4              |     40      |
|   Bare metal  | bigFlows.pcap |       3          |     No    |   4 GB   |  4  |     5      | -                    |     40      |
|     Docker    | bigFlows.pcap |       3          |     No    |   2 GB   |  4  |     5      | -                    |     40      |
| Docker + vtap | bigFlows.pcap |       3          |    Yes    |   2 GB   |  4  |     5      | -                    |     40      |
|       VM      | bigFlows.pcap |       3          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4              |     40      |
|   Bare metal  | bigFlows.pcap |       4          |     No    |   4 GB   |  4  |     5      | -                    |     40      |
|     Docker    | bigFlows.pcap |       4          |     No    |   2 GB   |  4  |     5      | -                    |     40      |
| Docker + vtap | bigFlows.pcap |       4          |    Yes    |   2 GB   |  4  |     5      | -                    |     40      |
|       VM      | bigFlows.pcap |       4          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4              |     40      |
|   Bare metal  | bigFlows.pcap |       8          |     No    |   4 GB   |  4  |     5      | -                    |     30      |
|     Docker    | bigFlows.pcap |       8          |     No    |   2 GB   |  4  |     5      | -                    |     25      |
| Docker + vtap | bigFlows.pcap |       8          |    Yes    |   2 GB   |  4  |     5      | -                    |     25      |
|       VM      | bigFlows.pcap |       8          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4              |     30      |
|   Bare metal  | bigFlows.pcap |       16         |     No    |   4 GB   |  4  |     5      | -                    |     10      |
|     Docker    | bigFlows.pcap |       16         |     No    |   2 GB   |  4  |     5      | -                    |     10      |
| Docker + vtap | bigFlows.pcap |       16         |    Yes    |   2 GB   |  4  |     5      | -                    |     10      |
|       VM      | bigFlows.pcap |       16         |    Yes    |   2 GB   |  4  |     5      | vCPUs=4              |     10      |
|     Docker    | bigFlows.pcap |       4          |     No    | 1024 MB  |  4  |     5      | -                    |     30      |
| Docker + vtap | bigFlows.pcap |       4          |    Yes    | 1024 MB  |  4  |     5      | -                    |     30      |
|       VM      | bigFlows.pcap |       4          |    Yes    | 1024 MB  |  4  |     5      | vCPUs=4              |     40      |
|     Docker    | bigFlows.pcap |       4          |     No    | 512 MB   |  4  |     5      | -                    |     10      |
| Docker + vtap | bigFlows.pcap |       4          |    Yes    | 512 MB   |  4  |     5      | -                    |     10      |
|       VM      | bigFlows.pcap |       4          |    Yes    | 512 MB   |  4  |     5      | vCPUs=4              |     30      |
|   Bare metal  | snort.log.1425823194 |       1          |     No    |   4 GB   |  4  |     5      | stat=1s       |      30     |
|     Docker    | snort.log.1425823194 |       1          |     No    |   2 GB   |  4  |     5      | stat=1s       |      30     |
| Docker + vtap | snort.log.1425823194 |       1          |    Yes    |   2 GB   |  4  |     5      | stat=1s       |      30     |
|       VM      | snort.log.1425823194 |       1          |    Yes    |   2 GB   |  4  |     5      | stat=1s, vCPUs=4 |   30     |
|   Bare metal  | snort.log.1425823194 |       2          |     No    |   4 GB   |  4  |     5      | stat=1s       |      30     |
|     Docker    | snort.log.1425823194 |       2          |     No    |   2 GB   |  4  |     5      | stat=1s       |      30     |
| Docker + vtap | snort.log.1425823194 |       2          |    Yes    |   2 GB   |  4  |     5      | stat=1s       |      30     |
|       VM      | snort.log.1425823194 |       2          |    Yes    |   2 GB   |  4  |     5      | stat=1s, vCPUs=4 |   30     |
|   Bare metal  | snort.log.1425823194 |       4          |     No    |   4 GB   |  4  |     5      | stat=1s       |      30     |
|     Docker    | snort.log.1425823194 |       4          |     No    |   2 GB   |  4  |     5      | stat=1s       |      30     |
| Docker + vtap | snort.log.1425823194 |       4          |    Yes    |   2 GB   |  4  |     5      | stat=1s       |      30     |
|       VM      | snort.log.1425823194 |       4          |    Yes    |   2 GB   |  4  |     5      | stat=1s, vCPUs=4 |   30     |

Notes

 * From the perspective of physical host, neither Docker nor QEMU strictly enforces this memory limit. The actual memory usage can go
   slightly higher.

 * For some test setups, the variation is so low that it's not worth repeating many times. For some tests the variation is high and more 
   rounds are run to get satisfiably large sample. Some tests were run significantly more times because the test scripts were copied and
   pasted.

 * The number of CPU cores is not manipulated because we can gain insight from different load levels. Actually CPU is the bottleneck for most
   test setups.

We ran each test multiple times to generate a number of samples (as shown the sample size column). Before running every test, the
receiver host is rebooted to make sure system state is restored back to original. After all samples are generated, we use the median of
all samples at each checkpoint to obtain an average result of the test. We then compare the average results of tests.

The script to parse raw CSV / Suricata eve.json files is hosted in [`dataparser/`](dataparser/) directory.

Note: after a test is run, all generated log files will be transferred to server cap08 using `rsync`. There are occasional glitches on
public network which could cause failure (connection timeout) of transmission. This is the reason why the sample size of some tests are
slightly smaller. I don't know why the clusters become inaccessible during those minutes.

## Result

We analyze the results of the two trace files, respectively.

### bigFlows.pcap

#### Throughput

The following is the recorded throughput of trace `bigFlows.pcap` when played by _one_ TCPreplay process. When there are two, three, or four TCPreplay processes, the throughput is simply multiplied because the sender host is not saturated in terms of CPU, memory, or NIC throughput. This can be confirmed by the system stat log of sender host.

![Throughput of bigFlows.pcap](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,%20NETOUT_BM_1X.pdf.svg)

In the following sections, I'll use "load" to mean a unit of TCPreplay process. For example, "2X load" means using two concurrent TCPreplay processes.

#### Comparing CPU Usage of Four Setups

It takes about 8 seconds for Suricata to initialize for all four setups. After Suricata loads, the sender will start replaying the trace.

At 1X load, we see that Docker and DockerV setups use almost the same amount of CPU share as that of bare metal setup, fluctuating near 25%, whereas the VM raises the host CPU usage to a range between 200% and 350%. The CPU usage of VM setup fluctuates greatly but is highly correspondent to the trace throughput. Note that when the VM runs without Suricata, the host CPU usage is about 2% to 5%.

![CPU Usage of Four Setups at 1X Load](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,%20CPU_1X.pdf.svg)

At 2X load level, we see that the CPU usage of bare metal, Docker, and DockerV setups doubles but still close to each other, and the VM setup has host CPU saturated.

![CPU Usage of Four Setups at 2X Load](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,%20CPU_2X.pdf.svg)

3X and 4X load levels reveal similar result -- CPU usage tripled and quadrupled, respectively, compared to 1X load level, and VM setup consumed all host CPU resource.

![CPU Usage of Four Setups at 3X Load](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,%20CPU_3X.pdf.svg)

![CPU Usage of Four Setups at 4X Load](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,%20CPU_4X.pdf.svg)

##### Comparing CPU Usage of Bare Metal and Docker Setups

Here is a diagram that puts the CPU usage of all setups except for VM and at ll load levels:

![CPU Usage of Setups excl. VM at Various Loads](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,%20CPU_XCPT_KVM.pdf.svg)

We see that Docker layer imposes trivial (with respect to overall CPU usage) overhead to host CPU when Suricata inspects the trace traffic at all four load levels.

But what's the overhead of macvtap traffic mirroring?

##### CPU Overhead of Docker and Macvtap

By comparing the CPU usage of Bare metal, Docker, and DockerV setups, we can gain insight on how much overhead Docker and macvtap introduces, respectively:

![CPU Usage Overhead of Macvtap](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,%20CPU_VTAP.pdf.svg)

While the CPU usage overhead of Docker is trivial at 4X load, there is a roughly 0% to 5% increase in CPU usage with macvtap, depending on traffic throughput. Note that we found macvtap of mode "passthrough" (requiring VT-d and SR-IOV) and model "virtio" the approach that incurs the least overhead compared to other ways of redirecting traffic including bridging, Virtual Ethernet Port Aggregator (VEPA), etc. With other approaches of redirecting traffic, the overhead can go higher.

By making this comparison we see that

 - By exposing the host NIC directly to Docker container, the overhead of mirroring traffic can be saved.
 - The high CPU usage of VM setup is not caused by macvtap traffic redirection; however, the CPU resource needed to redirect traffic it not negligible.

#### Comparing Memory Usage of Four Setups

The result of memory usage is so simple that they can be put in one diagram:

![Memory Usage of Four Setups](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,%20MEM_ALL.pdf.svg)

We see that increasing the load level barely increases the host memory usage on bare metal, Docker, and Docker with vtap setups. However, increasing load level dramatically increases the host memory usage on VM setup.

Note that even though after 150 seconds the memory usage of 2X, 3X, 4X load levels is about the same for VM setups, for those load levels, it's the host CPU that is a bottleneck. This prevents Suricata from increasing speed and taking more memory, and also explains why the memory usage there slightly decreases as load increases -- CPU is saturated and the system needs more CPU time to handle the network traffic, making Suricata run with even less resource. It's still noteworthy that for VM setup when CPU is not a bottleneck, the host observes an up to 15% memory usage increase. I therefore conjecture that if CPU were not a bottleneck, the memory usage will go spectacularly higher.

In terms of overhead, while the bare metal consumes about 10% of CPU usage, Docker setups impose trivial memory head, whereas the VM setup can eat three times as much, resulting in a up to 250% overhead when busy and 300% when idle.

##### Memory Usage inside KVM 

We also investigate how much memory is used inside VM and on host. From the graph below we see that the VM has not saturated its 2GB memory limit. We therefore understand that for our test setups memory is not a bottleneck.

![Memory Usage inside VM and on host](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,VM,sysstat,MEM.pdf.svg)

#### Comparing Performance of Suricata in Four Setups

Suricata exports performance metric in intervals of, by default, 8 seconds, to log files. We examine the log file and compare the following metrics:

 * _capture.kernel_packets_: The accumulative number of packets Suricata has captured.
 * _capture.kernel_drops_: The accumulative number of packets Suricata has dropped.
 * _decoder.pkts_: The accumulative number of packets Suricata has decoded.
 * _decoder.bytes_: The accumulative amount of data, in Bytes, Suricata has decoded. We post processed the data to use unit of KiB rather than B.

We do not examine the number of alerts triggered because it's highly affected by packet dropping.

##### Packet Capturing

We see that in all four load levels we use, packet capturing is about the same for all four setups. However, the VM setup tends to receive less packets in the end. Usually TCPreplay ends at second 312 and we send SIGTERM signal to Suricata 30 seconds after and wait for it to exit gracefully. It's very likely that for VM setup it still has packets yet to capture when exiting, resulting in the discrepancy we see here.

![Cumulative Packet Captured by Suricata in Four Setups](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,eve,CAPTURE.pdf.svg)

##### Packet Dropping

Packet dropping is a sign that Suricata can't process the workload given the resource it can utilize. Only VM setup observes packet drop starting from 2X load, and almost all increased load beyond 2X is dropped.

![Cumulative Packet Dropped by Suricata in Four Setups](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,eve,DROP.pdf.svg)

##### Data Decoding

Because the data cannot fit well in one graph, we first compare Docker setups with bare metal, and then VM setup with baremetal.

We first compare Docker and DockerV setups with bare metal, and see that there is no nontrivial difference between the three. In this case, there is no need to compare the number of bytes decoded because they will be on par with each other.

![Cumulative Data Decoded in Packets by Suricata, Bare metal vs Docker](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,eve,Decoded_Pkts_BM_vs_Dockers.pdf.svg)

We then compare VM setup with bare metal.

![Cumulative Data Decoded in Packets by Suricata, Bare metal vs Docker](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,eve,BM_vs_KVM.pdf.svg)

We see that while the decoding speed is comparable at 1X load, the decoding speed of VM Suricata is significantly lower as load increases from 2X to 4X, and there is no difference in decoding between 3X load and 4X load, which indicates that Suricata is saturated.

If we switch unit to KBytes, we see that as load increases, Suricata in VM runs slower and slower.

![Cumulative Data Decoded in KBytes by Suricata, Bare metal vs Docker](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,1-4,eve,Decoded_Bytes_BM_vs_KVM.pdf.svg)

#### When Memory Is Also a Bottleneck

In the previous tests, we set memory limit of 2GB which turns out sufficient for all setups and all four load levels. In this part we change memory limit to 512MB and see how resource usage and performance would change. From our previous tests we see that even 512MB is sufficient for 1X load on VM yet CPU becomes bottleneck of VM since 2X load. While we could tweak the parameters to isolate the CPU bottleneck, it's also reasonable to change the memory limit and observe the difference. Note that we did test with 1GB memory limit, but it turns out no difference from 2GB limit since VM's CPU bottleneck prevented VM from consuming more memory.

Therefore we compare the following two setups: DockerV versus VM under 512MB memory limit and 4X load. We choose those two setups so that the overhead of macvtap appears on both sides. For convenience we include their 2GB counterparts in the graphs.

##### Host CPU Usage

We see that 512MB has no effect on DockerV setup, but the CPU usage starts to decrease for 512MB VM since around 150 second. As we will see in a later graph, VM memory saturates there and thrashing occurs.

![Host CPU Usage, DockerV vs VM](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,4,512MB,CPU_2G_vs_512M.pdf.svg)

##### Host Memory Usage

There is not much to say about host memory usage. There is no difference between 2GB limit and 512MB limit in DockerV setup, while the VM memory hits its limit and cannot increase further. The memory increase after the point of thrashing is largely due to host caching the disk swap I/O of VM.

![Host Memory Usage, DockerV vs VM](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,4,512MB,MEM_2G_vs_512M.pdf.svg)

##### Memory Usage in VM

Memory usage in VM confirms that thrashing starts after approx. 150 seconds. We will inspect the memory usage drop near 328 second with behavior of Suricata.

![Host Memory Usage, DockerV vs VM](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,4,512MB,VM,sysstat,MEM.pdf.svg)

##### Performance of Suricata

We see that Suricata in DockerV setup shows no difference in performance given the two memory limits as the lines for their packet captured match well, and neither drop any packets. KVM with 2GB memory limit matches the DockerV packet captured line well until near the end; its lack of CPU power makes it impossible for Suricata to finish with all packets within the given time frame.

What's worth noting is that the graph seems to indicate that 512MB KVM Suricata captures more packets than other scenarios. However, this is not the case. Memory thrashing inside VM drifts Suricata's logging intervals (in unit of seconds), and when we put all series into one X-axis the drift is assumed non-existent even though it gets increasingly severe as time goes by. This can be verified by comparing the raw statistics of NIC traffic on host and inside VM manually.

![Host Memory Usage, DockerV vs VM](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,4,512MB,EVE,Capture,Drop.pdf.svg)

We see that Suricata inside 512MB VM is struggling to make slow progress, while Suricata in 512MB DockerV works just fine. Note that the slight drop of the line for 512MB KVM near 360 second is caused by the fact that we take medians of samples.

![Host Memory Usage, DockerV vs VM](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data/diagrams/bigFlows.pcap,4,512MB,EVE,Decode_KB.pdf.svg)

#### Increasing the Load Level

From result of other test configurations, we see that Docker setup is on a par with bare metal in terms of both resource usage and performance, up to 32X load level, beyond which we did not test since the sender host would be overly saturated.

#### Why is Suricata in VM that slow?

To further investigate how Suricata consumes way more CPU in VM than in bare metal, we use
[oprofile](http://oprofile.sourceforge.net/) to profile the execution of Suricata with 4X load in bare metal and in VM, respectively.
The result is hosted in [`oprofile_data/`](oprofile_data/) directory.

The function calls that consume most of (aggregated) CPU time on host execution are:

```
samples  %        linenr info                 app name                 symbol name
3079940  48.7275  util-cpu.c:190              suricata                 UtilCpuGetTicks
889800   14.0775  util-mpm-ac.c:1307          suricata                 SCACSearch
573918    9.0799  detect.c:1237               suricata                 SigMatchSignatures
```

While the function calls that consume most of CPU time on VM execution are:

```
samples  %        linenr info                 app name                 symbol name
3876496  77.4428  util-cpu.c:190              suricata                 UtilCpuGetTicks
378915    7.5698  detect.c:1237               suricata                 SigMatchSignatures
144521    2.8872  util-mpm-ac.c:1307          suricata                 SCACSearch
78725     1.5727  util-profiling.c:994        suricata                 SCProfileRuleStart
```

We see that the function `UtilCpuGetTicks()` consumes about 48.73% of CPU time of Suricata process on bare metal whereas it consumes
77.44% in KVM. With detailed report from oprofile we see that it is the seven processing threads that rely heavily on this function,
whereas the four management threads do not.

We then wonder which instruction in this function takes most time. Assembly wise, on host

```
0000000000736ca0 <UtilCpuGetTicks>: /* UtilCpuGetTicks total: 3079940 48.7275 */
 19614  0.3103 :  736ca0:	push   %rbx
  1345  0.0213 :  736ca1:	xor    %eax,%eax
               :  736ca3:	cpuid  
1281367 20.2724 :  736ca5:	rdtsc  
391861  6.1996 :  736ca7:	mov    %edx,%edi
    20 3.2e-04 :  736ca9:	mov    %eax,%esi
               :  736cab:	xor    %eax,%eax
               :  736cad:	cpuid  
1300635 20.5772 :  736caf:	mov    %rdi,%rax
 33929  0.5368 :  736cb2:	pop    %rbx
 51165  0.8095 :  736cb3:	shl    $0x20,%rax
     4 6.3e-05 :  736cb7:	or     %rsi,%rax
               :  736cba:	retq   
               :  736cbb:	nopl   0x0(%rax,%rax,1)
```

while in KVM

```
0000000000736ca0 <UtilCpuGetTicks>: /* UtilCpuGetTicks total: 3876496 77.4428 */
  3201  0.0639 :  736ca0:	push   %rbx
   421  0.0084 :  736ca1:	xor    %eax,%eax
     1 2.0e-05 :  736ca3:	cpuid  
1760507 35.1706 :  736ca5:	rdtsc  
159997  3.1963 :  736ca7:	mov    %edx,%edi
     5 1.0e-04 :  736ca9:	mov    %eax,%esi
               :  736cab:	xor    %eax,%eax
  2477  0.0495 :  736cad:	cpuid  
1783625 35.6324 :  736caf:	mov    %rdi,%rax
110918  2.2159 :  736cb2:	pop    %rbx
 55341  1.1056 :  736cb3:	shl    $0x20,%rax
     3 6.0e-05 :  736cb7:	or     %rsi,%rax
               :  736cba:	retq   
               :  736cbb:	nopl   0x0(%rax,%rax,1)
```

We find that it takes significantly more (aggregated) time to read x86 Timestamp Counter (TSC) register as the instruction `rdtsc`
shows, and to move register value from `%rdi` to `%rax`.

Unfortunately we fail to obtain a callgraph from oprofile which could let us know the reason why it spends more time on those
instructions -- is it simply because those instructions run slowly in VM? Or is it because this function is triggered more frequently?

To investigate this, we copy the source code of `UtilCpuGetTicks` into separate C file [test_rtdsc.c](test_rdtsc/test_rdtsc.c), and write a `main` function that calls this function 10^8 times. We run this program in both bare metal and VM, measuring how much time it takes to finish with `time` command, and the distribution of time onto the instructions with oprofile. The raw result is saved in [test_rdtsc/](test_rdtsc/) directory.

We find that it takes only 6.6 seconds (43.35% attributable to `rdtsc`) in bare metal, but 126.09 seconds (47.90% attributable to
`rdtsc`) inside VM. We also note that the instruction to update the loop counter, which is the first instruction after `cpuid`, also
takes significant amount of time (44.34% in bare metal; 47.44% in VM).

According to [Table 21-6, Intel Manual Volume 3B, pp.21-13](http://www.intel.com/Assets/en_US/PDF/manual/253669.pdf), the instruction
`rdtsc` could trigger a VM exit, making the instruction expensive in VM environment.

The instruction `cpuid` is often paired with `rdtsc` to prevent `rdtsc` from being executed out-of-order:

> In order to keep the RDTSC instruction from being performed out-of-order, a serializing instruction is required. A
> serializing instruction will force every preceding instruction in the code to complete before allowing the program to
> continue. One such instruction is the CPUID instruction, which is normally used to identify the processor on which
> the program is being run. For the purposes of this paper, the CPUID instruction will only be used to force the
> in-order execution of the RDTSC instruction.

-- [Coorporation, I. (1997). Using the RDTSC Instruction for Performance Monitoring. Techn. Ber., tech. rep., Intel Coorporation, 22.](https://www.ccsl.carleton.ca/~jamuir/rdtscpm1.pdf)

With a tool provided in QEMU repository written by Avi Kivity <avi@redhat.com>, we can check the "Primary Processor-Based VM-Execution
Controls" of our test CPU:

```
sudo ./vmxcap.py    Basic VMX Information
  Revision                                 14
  VMCS size                                1024
  VMCS restricted to 32 bit addresses      no
  Dual-monitor support                     yes
  VMCS memory type                         6
  INS/OUTS instruction information         yes
  IA32_VMX_TRUE_*_CTLS support             yes
pin-based controls
  External interrupt exiting               yes
  NMI exiting                              yes
  Virtual NMIs                             yes
  Activate VMX-preemption timer            yes
  Process posted interrupts                no
primary processor-based controls
  Interrupt window exiting                 yes
  Use TSC offsetting                       yes
  HLT exiting                              yes
  INVLPG exiting                           yes
  MWAIT exiting                            yes
  RDPMC exiting                            yes
  RDTSC exiting                            yes
  CR3-load exiting                         default
  CR3-store exiting                        default
  CR8-load exiting                         yes
  CR8-store exiting                        yes
  Use TPR shadow                           yes
  NMI-window exiting                       yes
  MOV-DR exiting                           yes
  Unconditional I/O exiting                yes
  Use I/O bitmaps                          yes
  Monitor trap flag                        yes
  Use MSR bitmaps                          yes
  MONITOR exiting                          yes
  PAUSE exiting                            yes
  Activate secondary control               yes
secondary processor-based controls
  Virtualize APIC accesses                 yes
  Enable EPT                               yes
  Descriptor-table exiting                 yes
  Enable RDTSCP                            yes
  Virtualize x2APIC mode                   yes
  Enable VPID                              yes
  WBINVD exiting                           yes
  Unrestricted guest                       no
  APIC register emulation                  no
  Virtual interrupt delivery               no
  PAUSE-loop exiting                       no
  RDRAND exiting                           no
  Enable INVPCID                           no
  Enable VM functions                      no
  VMCS shadowing                           no
  RDSEED exiting                           no
  EPT-violation #VE                        no
  Enable XSAVES/XRSTORS                    no
VM-Exit controls
  Save debug controls                      default
  Host address-space size                  yes
  Load IA32_PERF_GLOBAL_CTRL               yes
  Acknowledge interrupt on exit            yes
  Save IA32_PAT                            yes
  Load IA32_PAT                            yes
  Save IA32_EFER                           yes
  Load IA32_EFER                           yes
  Save VMX-preemption timer value          yes
VM-Entry controls
  Load debug controls                      default
  IA-32e mode guest                        yes
  Entry to SMM                             yes
  Deactivate dual-monitor treatment        yes
  Load IA32_PERF_GLOBAL_CTRL               yes
  Load IA32_PAT                            yes
  Load IA32_EFER                           yes
Miscellaneous data
  VMX-preemption timer scale (log2)        5
  Store EFER.LMA into IA-32e mode guest control no
  HLT activity state                       yes
  Shutdown activity state                  yes
  Wait-for-SIPI activity state             yes
  IA32_SMBASE support                      no
  Number of CR3-target values              4
  MSR-load/store count recommendation      0
  IA32_SMM_MONITOR_CTL[2] can be set to 1  no
  VMWRITE to VM-exit information fields    no
  MSEG revision identifier                 0
VPID and EPT capabilities
  Execute-only EPT translations            yes
  Page-walk length 4                       yes
  Paging-structure memory type UC          yes
  Paging-structure memory type WB          yes
  2MB EPT pages                            yes
  1GB EPT pages                            no
  INVEPT supported                         yes
  EPT accessed and dirty flags             no
  Single-context INVEPT                    yes
  All-context INVEPT                       yes
  INVVPID supported                        yes
  Individual-address INVVPID               yes
  Single-context INVVPID                   yes
  All-context INVVPID                      yes
  Single-context-retaining-globals INVVPID yes
VM Functions
  EPTP Switching                           no
```

So for our test environment `rdtsc` IS yielding VM exiting, and combined with `cpuid`, giving huge performance penalty to Suricata
running inside a virtual machine.

#### Summary

We see that Docker incurs trivial resource overhead compared to bare metal, while KVM's overhead is order of magnitude more than what
Suricata itself uses. In terms of performance, while Docker imposes negligible, if any, penalty, KVM makes it much less efficient to
run Suricata's instructions and makes CPU a bottleneck at relatively low load levels.

### snort.log.1425823194

#### Throughput

The trace file `snort.log.1425823194` sends high volume of data in short period of time (about 22 seconds). Data is collected with granularity of 1 second.

![Throughput of snort.log trace file](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data2/diagrams/snort.log.netout_1x.pdf.svg)

#### Performance of Suricata

The final result of the tests is as follows.

|   Setup    | Load | Time | Dropped.Pkts | Decoded.Pkts | Decoded.B  |
|:----------:|:----:|:----:|:------------:|:------------:|:----------:|
| Bare Metal |  1X  | 29 s |       0      |    142202    |  157287081 |
|   Docker   |  1X  | 28 s |       0      |    142202    |  157287081 |
|  DockerV   |  1X  | 26 s |       0      |    142203    |  157287081 |
|     KVM    |  1X  | 18 s |     18788    |     71412    |   79238466 |
| Bare Metal |  2X  | 28 s |       0      |    284404    |  314574162 |
|   Docker   |  2X  | 27 s |       0      |    284404    |  314574162 |
|  DockerV   |  2X  | 26 s |       0      |    284405    |  314574232 |
|     KVM    |  2X  | 18 s |     98456    |     81927    |   90416861 |
| Bare Metal |  4X  | 29 s |     67126    |    500749    |  552477875 |
|   Docker   |  4X  | 27 s |     67064    |    500793    |  553071996 |
|  DockerV   |  4X  | 27 s |     81282    |    487527    |  537692948 |
|     KVM    |  4X  | 18 s |    277529    |     81260    |   89281369 |

Note: Time column is the amount of time it takes to reach stable value. Because we take medians of all samples to form a representation, at least half samples complete by that time.

We see that in terms of performance Docker setup is on a par with bare metal even when CPU is stressed at 4X load. Macvtap consumes CPU, resulting in DockerV setup dropping more packets than Docker setup at 4X load, but it is still in the same magnitude as Docker and bare metal setups.

The result of VM setup is noteworthy. Not only it drops significantly more packets, but a nontrivial portion of packets (358789 captured / 568808 total) isn't even captured. In the following section, we will dive deeper into what happens to VM setup at 4X load.

#### Investigating the VM Issue

The following graph puts the cumulative number of packets sent (light blue line), cumulative number of packets received on the VM (orange line), cumulative number of packets captured (gray bar) / dropped (yellow bar) / decoded (dark blue bar) by Suricata, host CPU usage (green line, percentage), and VM memory usage (dark blue line, percentage) together:

![Packet Processing and Resource Usage of VM setup at 4X load](https://rawgithub.com/xybu/cs590-nfv/master/experiments/suricata/data2/diagrams/snort.log.vm_packet_res_4x.pdf.svg)

Note that because we are taking medians, cumulative number of packets sent is not necessarily equal to cumulative number of packets received. I manually inspected several instances and for those instances they are indeed equal.

We see from the graph that Suricata packet capturing thread(s) never manages to process packets that come every single second. Most new packets are dropped and few are decoded. CPU usage reaches ceiling near second 10 and remains high for a few seconds. My guess is that because Suricata can't read packets fast enough, the kernel buffer to hold packets becomes full and new packets are simply dropped. When Suricata catches up it no longer finds more packets to process.

After further checking, it turns out the the performance degradation is largely due to the fact that X86 `rdtsc` instruction cannot
run efficiently in VM environment. It's mostly used to get precise timestamps for profiling purposes. Turning down rate of
profiling could mitigate the issue, but cannot solve it.

## Conclusion

We see that container solutions like Docker are way more suitable than virtual machines for light-weight programs like Suricata in that (1) less resource is needed, and (2) the high cost of VM exiting triggered by some instructions can be saved.
