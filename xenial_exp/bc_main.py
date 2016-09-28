import argparse
import bc_modes


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark Suricata / Snort inside a specified environment on remote host and collect system info.')
    parser.add_argument('mode', type=str, help='Which mode, bare metal (bm), Docker (docker), VM (vm) to run in.')
    parser.add_argument('trace', type=str, help='Name of a trace file in trace repository.')
    parser.add_argument('nworkers', type=int, help='Number of concurrent TCPreplay processes.')
    parser.add_argument('--src-nic', '-s', nargs='?', type=str, default='enp32s0', help='Replay trace on this local NIC.')
    parser.add_argument('--dest-nic', '-d', nargs='?', type=str, default='enp34s0',
                        help='Trace will be observed on this NIC on the remote host.')
    parser.add_argument('--outfile', nargs='?', type=str, default='suricata.out',
                        help='Name of the file to save output of Suricata / Snort.')

    # Arguments used in all modes.
    parser.add_argument('--macvtap', default=False, action='store_true',
                        help='If present, create a macvtap device of dest NIC on remote host and observe it.')
    parser.add_argument('--swappiness', '-w', nargs='?', type=int, default=5,
                        help='Memory swappiness of the container (e.g., 5).')

    # Arguments used by sysmon.
    parser.add_argument('--mon-interval-sec', nargs='?', type=int, default=2,
                        help='Interval, in sec, between collecting remote host info.')

    # Arguments used by TCPreplay.
    parser.add_argument('--trace-speed', nargs='?', type=float, default=1.0,
                        help='Speed of TCP replay (e.g., 2 for double the speed).')

    # Arguments used in Docker mode.
    parser.add_argument('--docker-image', nargs='?', type=str, default='xybu:suricata',
                        help='Name of the Docker image to create container from.')
    parser.add_argument('--docker-name', nargs='?', type=str, default='suricata',
                        help='Name of the container to create.')


    parser.add_argument('--memory', '-m', nargs='?', type=str, default='2g',
                        help='Memory limit of the Docker container (e.g., "2g", "512m").')
    parser.add_argument('--cpuset', '-c', nargs='?', type=str, default='0-3',
                        help='Set of CPUs the container can use (e.g., "0-3", "1,3-5").')


    parser.add_argument('--vm-name', '-n', nargs='?', type=str, default='ids-vm',
                        help='Name of the virtual machine registered to libvirt.')
    parser.add_argument('--vm-ip', '-i', nargs='?', type=str, default='dhcp',
                        help='IP address of the virtual machine (e.g., "192.168.122.2" or "dhcp").')
    parser.add_argument('--vm-nic', '-f', nargs='?', type=str, default='eth1',
                        help='Trace will be observed on this NIC in the VM (default: eth1). Must be configured by VM manually.')
    parser.add_argument('--memory', '-m', nargs='?', type=str, default='2g',
                        help='Memory limit of the virtual machine (e.g., "2g", "512m"). Must be integer number followed by "g", "m", or "k".')
    parser.add_argument('--vcpus', '-p', nargs='?', type=int, default=0,
                        help='Number of vCPUs for the virtual machine (e.g., 0=max).')
    parser.add_argument('--cpuset', '-c', nargs='?', type=str, default='0-3',
                        help='Set of CPUs the VM can use (e.g., "0-3", "1,3-5").')
    parser.add_argument('--swappiness', '-w', nargs='?', type=int, default=5,
                        help='Memory swappiness on host and in VM (e.g., 5).')
    parser.add_argument('--replay-speed', nargs='?', type=int, default=1,
                        help='Speed of TCP replay (e.g., 2 for double the speed).')


if __name__ == '__main__':
    main()
