#!/bin/bash -x

device_id="0000:22:00.0"

vfiobind() {
	dev="$1"
	vendor=$(cat /sys/bus/pci/devices/$dev/vendor)
	device=$(cat /sys/bus/pci/devices/$dev/device)
	if [ -e /sys/bus/pci/devices/$dev/driver ]; then
		echo $dev > /sys/bus/pci/devices/$dev/driver/unbind
	fi
	echo $vendor $device > /sys/bus/pci/drivers/vfio-pci/new_id
}

modprobe vfio-pci
vfiobind $device_id
echo -e "\033[92mCompleted VFIO binding.\033[0m"
