#!/usr/bin/python3

import argparse

from test_suricata import *


class TestSuricataDocker(TestSuricataBase):

	def __init__(self, args, container_name='suricata'):
		super().__init__()
		self.container_name = container_name
		self.args = args
		self.session_id = 'logs,docker,%d,%s,%d,%s,%s,%d,%s,%s,%d,%d' % (int(time.time()), args.trace, args.nworker, args.src_nic,
			args.dest_nic + '.vtap' if args.macvtap else args.dest_nic, args.interval, args.memory, args.cpuset, args.swappiness, args.replay_speed)
		self.session_tmpdir = RUNNER_TMPDIR + '/' + self.session_id
		self.local_tmpdir = TESTER_TMPDIR + '/' + self.session_id

	def prework(self):
		self.init_test_session(self.session_id, self.local_tmpdir, self.session_tmpdir, self.args)
		self.simple_call(['docker', 'rm', '-f', self.container_name])

	def remove_container(self):
		log('Removing container...')
		self.simple_call(['docker', 'stop', self.container_name])
		self.simple_call(['docker', 'rm', self.container_name])

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
			'--enable-ps', '--ps-keywords', 'suricata', 'docker', '--ps-outfile', 'psstat.docker.csv'],
			cwd=self.session_tmpdir, store_pid=True, allow_error=True, stdout=sys.stdout.buffer, stderr=sys.stdout.buffer)
		self.suricata_out = open(self.local_tmpdir + '/suricata.out', 'w')
		self.suricata_proc = self.shell.spawn(['docker', 'run', '-i', '--name', self.container_name, '--cpuset-cpus', self.args.cpuset,
			'--memory', self.args.memory, '--memory-swappiness', str(self.args.swappiness), '--net=host',
			'-v', '%s:%s' % (self.session_tmpdir, '/var/log/suricata'), 'xybu:suricata', 'suricata', '-i', dest_nic],
			stdout=self.suricata_out, stderr=self.suricata_out, encoding='utf-8', store_pid=True, allow_error=True)
		# Enable this monitor if we really need that much info.
		#self.docker_stat_proc = self.shell.spawn([RUNNER_TMPDIR + '/tester_script/dockerstat.py', self.container_name, '--out', 'docker.json', '--delay', str(self.args.interval)],
		#	cwd=self.session_tmpdir, store_pid=True, allow_error=True, stdout=sys.stdout.buffer, stderr=sys.stdout.buffer)
		self.wait_for_suricata(self.session_tmpdir)
		self.replay_trace(self.local_tmpdir, self.args.trace, self.args.nworker, self.args.src_nic, self.args.interval, self.args.replay_speed)
		self.remove_container()
		suricata_result = self.suricata_proc.wait_for_result()
		log('Suricata container returned with value %d.' % suricata_result.return_code)
		self.suricata_out.close()
		del self.suricata_proc
		del self.suricata_out
		#self.docker_stat_proc.send_signal(signal.SIGINT)
		self.sysmon_proc.send_signal(signal.SIGINT)
		#self.docker_stat_proc.wait_for_result()
		self.sysmon_proc.wait_for_result()
		#del self.docker_stat_proc
		del self.sysmon_proc
		if self.status == self.STATUS_START:
			self.status = self.STATUS_DONE

	def postwork(self):
		log('Postwork...')
		if self.status == self.STATUS_DONE:
			self.upload_test_session(self.session_id, self.local_tmpdir, self.session_tmpdir)

	def cleanup(self):
		log('Cleaning up...')
		if hasattr(self, 'suricata_proc'):
			self.remove_container()
		self.simple_call(['sudo', 'pkill', '-9', 'python'])
		if hasattr(self, 'sysmon_proc'):
			self.sysmon_proc.send_signal(signal.SIGKILL)
		#if hasattr(self, 'docker_stat_proc'):
		#	self.suricata_proc.send_signal(signal.SIGKILL)
		if hasattr(self, 'suricata_out'):
			self.suricata_out.close()
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
	parser = argparse.ArgumentParser(description='Run Suricata inside a Docker container on remote host and collect system info.')
	parser.add_argument('trace', type=str, help='Name of a trace file in trace repository.')
	parser.add_argument('nworker', type=int, help='Number of concurrent TCPreplay processes.')
	parser.add_argument('--src-nic', '-s', nargs='?', type=str, default='em2', help='Replay trace on this local NIC.')
	parser.add_argument('--dest-nic', '-d', nargs='?', type=str, default='em2', help='Trace will be observed on this NIC on the dest host.')
	parser.add_argument('--macvtap', '-v', default=False, action='store_true', help='If present, create a macvtap device on dest host.')
	parser.add_argument('--interval', '-t', nargs='?', type=int, default=4, help='Interval (sec) between collecting dest host info.')
	parser.add_argument('--memory', '-m', nargs='?', type=str, default='2g', help='Memory limit of the Docker container (e.g., "2g", "512m").')
	parser.add_argument('--cpuset', '-c', nargs='?', type=str, default='0-3', help='Set of CPUs the container can use (e.g., "0-3", "1,3-5").')
	parser.add_argument('--swappiness', '-w', nargs='?', type=int, default=5, help='Memory swappiness of the container (e.g., 5).')
	parser.add_argument('--replay-speed', nargs='?', type=int, default=1, help='Speed of TCP replay (e.g., 2 for double the speed).')
	args = parser.parse_args()
	log(str(args))
	TestSuricataDocker(args).start()


if __name__ == '__main__':
	main()
