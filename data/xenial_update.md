Notes Regarding Recent Software Updates
=======================================

Many software packages have updated since we conducted the experiment. Some important ones are:

 * `Ubuntu`: 15.10 -> 16.04.1
 * `GCC`: 4.8.4 -> 5.4.0
 * `Docker`: 1.11.0 -> 1.21.1
 * `Suricata`: 3.0.1 -> 3.1.2

Some updates indeed bring performance improvements.

# Performance Improvement of Suricata

A series of updates of Suricata, namely, [`3.1`](https://suricata-ids.org/2016/06/20/suricata-3-1-released/), [`3.1.1`](https://suricata-ids.org/2016/07/13/suricata-3-1-1-released/), [`3.1.2`](https://suricata-ids.org/2016/09/07/suricata-3-1-2-released/) brought many performance improvements to this software. Some highlights are:

* Use [HyperScan](http://www.intel.com/content/dam/www/public/us/en/documents/solution-briefs/hyperscan-suricata-solution-brief.pdf) as the default pattern matching library (3.1). Intel benchmark reveals huge performance improvement. __Our testbeds, however, do not support AVX/AVX2 instruction sets and can't make full use of HyperScan. Therefore we did not test this factor.__
* Detection engine is rewritten to improve memory usage, bootstrap time, and performance (3.1).
* Optimized lock (3.1), TCP and IPv6 decoder (3.1), and AF_PACKET support (3.1, 3.1.1).

Behavior-wise we see that Suricata 3.1.x uses by default 4 mgmt threads and 4 pkt processing threads on our 4-core test machine, while Suricata 3.0.1 used by default 4 mgmt threads and 7 pkt processing threads. Fewer number of threads results in fewer calls to `UtilCpuGetTicks()` as well.

## Suricata 3.1.2

We updated Suricata to 3.1.2 in VM and redo the experiment on old VM setup. By comparing the [new excel sheet](https://github.com/xybu/cs590-nfv/blob/master/data/suricata_v312/vm%2CbigFlows.pcap%2C4%2Cem2%2Cenp34s0%2C1%2C2g%2C4%2C0-3%2C5%2Csuricata-vm%2Cdhcp%2Ceth1%2C1%2Ceve.xlsx) with the [old excel sheet](https://github.com/xybu/cs590-nfv/blob/master/experiments/suricata/data/vm%2CbigFlows.pcap%2C4%2Cem2%2Cenp34s0%2C4%2C2g%2C4%2C0-3%2C5%2Csuricata-vm%2Cdhcp%2Ceth1%2C1%2Ceve.xlsx) we see that Suricata managed to capture more packets and decode most of them.

| Suricata | Total.Sent.Pkts | Captured.Pkts | Drop.Pkts | Decoded.Pkts | Decoded.KB |
|----------|-----------------|---------------|-----------|--------------|------------|
|   3.1.2  |   3166460       |    3081408    |   33046   |    3048538   | 1331173.01 |
|   3.0.1  |   3166460       |    3072473    |  1612954  |    1458653   | 546008.40  |

## Resource Usage of Suricata

Great difference is observed for VM setup. We see that Suricata 3.1.2 uses much less CPU resource and about 30% less RAM than Suricata 3.0.1 (25% vs. 36%).

![Suricata 3.1.2](https://rawgithub.com/xybu/cs590-nfv/master/data/suricata312_vm_4x_cpu_ram.svg)

Recall that Suricata 3.0.1 in VM almost saturated the CPU at 1X bigFlows.pcap load.

![Suricata 3.0.1](https://rawgithub.com/xybu/cs590-nfv/master/data/suricata301_vm_4x_cpu_ram.svg)

Besides, we also saw an average of 41.15% reduction of CPU usage in bare metal (47.77% vs. 81.17%), but the difference of RAM usage is negligible.

## Is `rdtsc` faster in newer version of QEMU?

No it's not. The `test_rdtsc` program still takes ~128 seconds on avg to finish. Recall that in wily setup we have

> We find that it takes only 6.6 seconds (43.35% attributable to rdtsc) in bare metal, 
> but 126.09 seconds (47.90% attributable to rdtsc) inside VM.

Version of QEMU:

```
$ bu1@cap21:[~]: qemu-system-x86_64 --version
QEMU emulator version 2.5.0 (Debian 1:2.5+dfsg-5ubuntu10.4), Copyright (c) 2003-2008 Fabrice Bellard
The versions of Linux kernel and gcc for our Xenial VM are:
```

Versions of Linux kernel and GCC:

```
$ root@xenial-ids:/dev/shm/test_rdtsc# uname -a
Linux xenial-ids 4.4.0-38-generic #57-Ubuntu SMP Tue Sep 6 15:42:33 UTC 2016 x86_64 x86_64 x86_64 GNU/Linux
$ root@xenial-ids:/dev/shm/test_rdtsc# gcc -v
Using built-in specs.
COLLECT_GCC=gcc
COLLECT_LTO_WRAPPER=/usr/lib/gcc/x86_64-linux-gnu/5/lto-wrapper
Target: x86_64-linux-gnu
Configured with: ../src/configure -v --with-pkgversion='Ubuntu 5.4.0-6ubuntu1~16.04.2' --with-bugurl=file:///usr/share/doc/gcc-5/README.Bugs --enable-languages=c,ada,c++,java,go,d,fortran,objc,obj-c++ --prefix=/usr --program-suffix=-5 --enable-shared --enable-linker-build-id --libexecdir=/usr/lib --without-included-gettext --enable-threads=posix --libdir=/usr/lib --enable-nls --with-sysroot=/ --enable-clocale=gnu --enable-libstdcxx-debug --enable-libstdcxx-time=yes --with-default-libstdcxx-abi=new --enable-gnu-unique-object --disable-vtable-verify --enable-libmpx --enable-plugin --with-system-zlib --disable-browser-plugin --enable-java-awt=gtk --enable-gtk-cairo --with-java-home=/usr/lib/jvm/java-1.5.0-gcj-5-amd64/jre --enable-java-home --with-jvm-root-dir=/usr/lib/jvm/java-1.5.0-gcj-5-amd64 --with-jvm-jar-dir=/usr/lib/jvm-exports/java-1.5.0-gcj-5-amd64 --with-arch-directory=amd64 --with-ecj-jar=/usr/share/java/eclipse-ecj.jar --enable-objc-gc --enable-multiarch --disable-werror --with-arch-32=i686 --with-abi=m64 --with-multilib-list=m32,m64,mx32 --enable-multilib --with-tune=generic --enable-checking=release --build=x86_64-linux-gnu --host=x86_64-linux-gnu --target=x86_64-linux-gnu
Thread model: posix
gcc version 5.4.0 20160609 (Ubuntu 5.4.0-6ubuntu1~16.04.2)
```

# VFIO

We see that VFIO in general reduces CPU overhead and the spared resource can be used by application, and the heavier the traffic, the more CPU resource is saved. But VM+VFIO is by no means comparable to any container setup.

Another note is that after VFIO is enabled it seems that KVM no longer dynamically allocates memory for the VM. Behavior-wise for VM+VFIO setup (VM memory is set to 2GB) 2465MB of host memory is used after VM boots, while for VM+macvtap setup only 618MB memory is used.

## Impact of VFIO for Snort

Compare the performance of Snort in VM+VFIO with that of VM+macvtap. 

| Load | CPU Usage                | Performance                    | Note                 |
|------|--------------------------|--------------------------------|----------------------|
|  2X  | mean=-3.45, stdev=1.4875 | No significant difference.     | bigFlows.pcap        |
|  4X  | First part {mean=-3.69, stdev=5.27}, second part {mean=-40.03, stdev=12.73} | Drops 8% less packet. | bigFlows.pcap  |

 * Not sure what caused the great difference in the second part of 4X bigFlows.pcap. At 2X load the separation is not obvious.
 * For snort.log trace file no obvious difference is observed probably because (1) CPU usage is measured at 1 sec interval and doesn't align well, and (2) the duration of the trace file is short.

## Impact of VFIO for Suricata

| Load | CPU Usage                | Performance                    | Note                 |
|------|--------------------------|--------------------------------|----------------------|
|  2X  | mean=-3.85, stdev=3.6903 | No difference.                 | bigFlows.pcap        |
|  4X  | mean=-7.55, stdev=3.4549 | 1% less packet drop.           | bigFlows.pcap        |

# Ubuntu Xenial

For Snort, the impact of latest Ubuntu (16.04.1) and compiler (GCC 5.4) is trivial (< +-1% for all setups).
