Notes for SR-IOV
================

Expose host NIC directly to VM.

Some random links:

* The original link (Use VFIO):
http://www.linux-kvm.org/page/10G_NIC_performance:_VFIO_vs_virtio#Check_if_your_NIC_supports_SR-IOV

* How to assign devices with VT-d in KVM (read other examples as well):
http://www.linux-kvm.org/page/How_to_assign_devices_with_VT-d_in_KVM

* A script that might be useful later (DPDK):
https://github.com/scylladb/seastar/commit/09a0aab822a92d3921707647f21b2dfb19ed212f

* IBM's developers' guide for SR-IOV (concepts and more pointers):
http://www.ibm.com/developerworks/library/l-pci-passthrough/index.html

* oVirt's guide for SR-IOV (concepts):
https://wiki.ovirt.org/develop/release-management/features/engine/sr-iov/

* An example of using SR-IOV on RHEL (almost useless):
https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/5/html/Virtualization/sect-Para-virtualized_Windows_Drivers_Guide-How_SR_IOV_Libvirt_Works.html

* An example of VGA passthrough on Debian:
https://wiki.debian.org/VGAPassthrough#Hardware_Setup

* An example of NVIDIA card passthrough:
https://www.pugetsystems.com/labs/articles/Multiheaded-NVIDIA-Gaming-using-Ubuntu-14-04-KVM-585/#Step1EdittheUbuntumodulesandbootloader
What's important here is the kernel module list and grub config.

* Set up KVM passthrough:
http://askubuntu.com/questions/568621/tunner-card-pci-passthrough-on-kvmv
http://spica-and-roid.blogspot.com/2012_07_01_archive.html

* Difference between SR-IOV (NIC and VT-d) and PCI passthrough (requires VT-d)
https://www.paloaltonetworks.com/documentation/61/pan-os/newfeaturesguide/virtualization-features/kvm-support

* Set up host NIC passthrough with `virt-manager` GUI:
http://ask.xmodulo.com/pci-passthrough-virt-manager.html

* Or equivalently, the XML config for VM:
http://askubuntu.com/questions/119122/pci-passthrough-on-kvm
It's in the OP.

* If NIC eth not showing up -- `ifconfig -a` and see what happens.
http://superuser.com/questions/381804/ethernet-port-not-showing-up-in-ifconfig
