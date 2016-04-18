#!/usr/bin/python3

import argparse
import socket

from test_suricata import *


class TestSuricataVm(TestSuricataBase):

	def __init__(self, args, container_name='suricata'):
		super().__init__()
		self.container_name = container_name
		self.args = args
		self.session_id = 'logs,vm,%d,%s,%d,%s,%s,%d,%s,%d,%s,%d,%s,%s,%s,%d' % (int(time.time()), args.trace, args.nworker, args.src_nic,
			args.dest_nic + '.vtap' if args.macvtap else args.dest_nic, args.interval, args.memory, args.vcpus, args.cpuset, args.swappiness,
			args.vm_name, args.vm_ip, args.vm_nic, args.replay_speed)
		self.session_tmpdir = RUNNER_TMPDIR + '/' + self.session_id
		self.local_tmpdir = TESTER_TMPDIR + '/' + self.session_id

	def memory_to_kB(self, s):
		if s[-1] == 'g':
			return int(s[:-1]) << 20
		elif s[-1] == 'm':
			return int(s[:-1]) << 10
		elif s[-1] == 'k':
			return int(s[:-1])
		raise ValueError('Memory limit "%s" is not recognized or too low.' % s)

	def probe_vm_ip(self, vm_name):
		while True:
			log('Wait for 10sec to probe VM IP address from DHCP...')
			time.sleep(10)
			ret = self.shell.run(['virsh', 'net-dhcp-leases', 'default'], allow_error=True)
			for line in ret.output.decode('utf-8').split('\n'):
				print(line.strip().split())
				if vm_name in line:
					# "2016-04-12 01:13:28  52:54:00:fb:44:5b  ipv4      192.168.122.204/24        suricata-vm     -"
					return line.strip().split()[4].split('/')[0]

	def reboot_vm(self):
		# Shutdown VM if running.
		if self.simple_call(['virsh', 'shutdown', self.args.vm_name]) == 0:
			log('Wait for 20sec for VM shutdown...')
			time.sleep(20)
		# Configure VM resource allocation.
		if self.args.vcpus == 0:
			log('Detecting remote host CPU count...')
			self.args.vcpus = self.simple_call(['python3', '-c' 'import sys, psutil; sys.exit(psutil.cpu_count())'])
			if self.args.vcpus == 0:
				self.args.vcpus = 4
				log('Failed to detect remote host CPU count. Use default value 4.')
			else:
				log('Updated vcpus argument to %d.' % self.args.vcpus)
		self.simple_call(['virsh', 'emulatorpin', self.args.vm_name, self.args.cpuset, '--config'])
		self.simple_call(['virsh', 'setvcpus', self.args.vm_name, str(self.args.vcpus), '--config'])
		for i in range(self.args.vcpus):
			self.simple_call(['virsh', 'vcpupin', self.args.vm_name, '--vcpu', str(i), self.args.cpuset, '--config'])
		self.simple_call(['virsh', 'setmem', self.args.vm_name, str(self.memory_to_kB(self.args.memory)), '--config'])
		# Configure macvtap from dest_nic to VM.VM_NIC. VM_NIC must be up by VM in /etc/network/interfaces.
		# self.simple_call(['virsh', 'detach-interface', self.args.vm_name, 'direct', '--config'])
		# self.simple_call(['virsh', 'attach-interface', self.args.vm_name,
		#	'--type', 'direct',
		#	'--source', self.args.dest_nic,
		#	'--target', self.MACVTAP_NAME,
		#	'--mac', gen_random_mac_addr(),
		#	'--model', 'virtio',
		#	'--mode', 'passthrough'])
		# Start VM. Should succeed because VM was just shut down.
		self.simple_call(['virsh', 'start', self.args.vm_name])
		# Obtain VM IP address.
		if self.args.vm_ip.lower() == 'dhcp':
			self.args.vm_ip = self.probe_vm_ip(self.args.vm_name)
			log('IP address of VM is "%s".' % self.args.vm_ip)
		# Busy waiting for VM to start.
		while self.simple_call(['ssh', 'root@' + self.args.vm_ip, 'echo', 'Virtual machine is ready.']) != 0:
			log("Waiting for 10sec for virtual machine to boot...")
			time.sleep(10)

	def prework(self):
		self.init_test_session(self.session_id, self.local_tmpdir, self.session_tmpdir, self.args)
		self.reboot_vm()

	def run(self):
		self.status = self.STATUS_START
		nic = self.args.dest_nic
		dest_nic = self.args.dest_nic
		if self.args.macvtap:
			nic = nic + ',' + self.MACVTAP_NAME
			dest_nic = self.MACVTAP_NAME
		self.sysmon_proc = self.shell.spawn([RUNNER_TMPDIR + '/tester_script/sysmon.py',
			'--delay', str(self.args.interval), '--outfile', 'sysstat.receiver.csv',
			'--nic', nic, '--nic-outfile', 'netstat.{nic}.csv',
			'--enable-ps', '--ps-keywords', 'qemu', '--ps-outfile', 'psstat.qemu.csv'],
			cwd=self.session_tmpdir, store_pid=True, allow_error=True, stdout=sys.stdout.buffer, stderr=sys.stdout.buffer)
		# Could use virsh-top though.
		self.suricata_proc = self.shell.spawn([RUNNER_TMPDIR + '/tester_script/' + self.args.vm_name + '.py',
			self.args.vm_ip, '/tmp/test', self.args.vm_nic, str(self.args.swappiness), str(self.args.interval), '/var/log/suricata'],
			cwd=self.session_tmpdir, stdout=sys.stdout.buffer, stderr=sys.stdout.buffer, store_pid=True, allow_error=True)
		self.wait_for_suricata('/var/log/suricata', prepend=['ssh', 'root@' + self.args.vm_ip])
		self.replay_trace(self.local_tmpdir, self.args.trace, self.args.nworker, self.args.src_nic, self.args.interval, self.args.replay_speed)
		self.suricata_proc.send_signal(signal.SIGINT)
		suricata_result = self.suricata_proc.wait_for_result()
		log('Suricata VM script returned with value %d.' % suricata_result.return_code)
		del self.suricata_proc
		self.sysmon_proc.send_signal(signal.SIGINT)
		self.sysmon_proc.wait_for_result()
		del self.sysmon_proc
		if self.status == self.STATUS_START:
			self.status = self.STATUS_DONE

	def postwork(self):
		log('Postwork...')
		if self.status == self.STATUS_DONE:
			self.simple_call(['rsync', '-zvrpE', 'root@%s:%s/*' % (self.args.vm_ip, '/var/log/suricata'), self.session_tmpdir + '/'])
			self.simple_call(['rsync', '-zvrpE', 'root@%s:%s/*' % (self.args.vm_ip, '/tmp/test'), self.session_tmpdir + '/'])
			self.upload_test_session(self.session_id, self.local_tmpdir, self.session_tmpdir)

	def cleanup(self):
		log('Cleaning up...')
		if hasattr(self, 'suricata_proc'):
			self.suricata_proc.send_signal(signal.SIGKILL)
		self.simple_call(['sudo', 'pkill', '-9', 'python'])
		if hasattr(self, 'sysmon_proc'):
			self.sysmon_proc.send_signal(signal.SIGKILL)
		if hasattr(self, 'docker_stat_proc'):
			self.suricata_proc.send_signal(signal.SIGKILL)
		self.simple_call(['virsh', 'shutdown', self.args.vm_name])
		self.destroy_session(self.session_id, self.local_tmpdir, self.session_tmpdir, self.args)
		self.close()

	def start(self):
		try:
			self.prework()
			self.run()
			self.postwork()
			self.cleanup()
		except KeyboardInterrupt:
			log('Interrupted. Stopping and cleaning...')
			self.cleanup()


def main():
	parser = argparse.ArgumentParser(description='Run Suricata inside a virtual machine (managed by libvirt) on remote host and collect system info.')
	parser.add_argument('trace', type=str, help='Name of a trace file in trace repository.')
	parser.add_argument('nworker', type=int, help='Number of concurrent TCPreplay processes.')
	parser.add_argument('--src-nic', '-s', nargs='?', type=str, default='em2', help='Replay trace on this local NIC.')
	parser.add_argument('--dest-nic', '-d', nargs='?', type=str, default='enp34s0', help='Trace will be observed on this NIC on the dest host.')
	parser.add_argument('--macvtap', '-v', default=False, action='store_true', help='If present, create a macvtap device on dest host.')
	parser.add_argument('--interval', '-t', nargs='?', type=int, default=4, help='Interval (sec) between collecting dest host info.')
	parser.add_argument('--vm-name', '-n', nargs='?', type=str, default='suricata-vm', help='Name of the virtual machine registered to libvirt.')
	parser.add_argument('--vm-ip', '-i', nargs='?', type=str, default='dhcp', help='IP address of the virtual machine (e.g., "192.168.122.2" or "dhcp").')
	parser.add_argument('--vm-nic', '-f', nargs='?', type=str, default='eth1', help='Trace will be observed on this NIC in the VM (default: eth1). Must be configured by VM manually.')
	parser.add_argument('--memory', '-m', nargs='?', type=str, default='2g', help='Memory limit of the virtual machine (e.g., "2g", "512m"). Must be integer number followed by "g", "m", or "k".')
	parser.add_argument('--vcpus', '-p', nargs='?', type=int, default=0, help='Number of vCPUs for the virtual machine (e.g., 0=max).')
	parser.add_argument('--cpuset', '-c', nargs='?', type=str, default='0-3', help='Set of CPUs the VM can use (e.g., "0-3", "1,3-5").')
	parser.add_argument('--swappiness', '-w', nargs='?', type=int, default=5, help='Memory swappiness on host and in VM (e.g., 5).')
	parser.add_argument('--replay-speed', nargs='?', type=int, default=1, help='Speed of TCP replay (e.g., 2 for double the speed).')
	args = parser.parse_args()
	log(str(args))
	TestSuricataVm(args).start()


if __name__ == '__main__':
	main()
