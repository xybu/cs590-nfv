# Issues

 * Docker stat does not include resource usage outside cgroup. There are at
 least two docker processes besides what's inside a running container, and their
 resource usage can fluctuate depending on what's happening inside each running
 container. Therefore, it's not good not to include docker's overhead resource
 usage.

 * Docker's resource limit does not affect what's outside cgroup, that is,
 Docker daemon processes themselves.

 * It's not good to use `top` or `atop` to gather resource info by processes and
 sum them up, because the timestamps do not always match -- or one has to
 inspect manually.

 * `top` and `atop` have output that are not friendly for post-processing. In
 particular, `atop`'s CPU usage numbers -- if there are 4 cores, then one has to
 parse 5 lines for a single timestamp -- not ideal.

 * We shouldn't have used Ubuntu 14.04 LTS. The QEMU package is updated in 2008,
 and the libvirt, even with 3rd party repo, is updated in 2014. I have
 experienced a bug in libvirt 1.2.2 which is supposed to have been fixed.
 Installing those packages from source is difficult because of complex
 dependency and large code base.

 * April 8, 2016 is an awkward time because Ubuntu 16.04 LTS will be released in
 two weeks. This newer version maintains packages of much newer versions.

 * It turns out that the "CPU throttling" we observed is a problem with atop. 
 Other programs like htop, top, and my own monitor show that the CPU usage of
 qemu process is indeed 400%.
