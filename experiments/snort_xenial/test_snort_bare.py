#!/usr/bin/python3

import argparse

from test_snort import *


class TestSnortBareMetal(TestSnortBase):

	def __init__(self, args):
		super().__init__()
		self.args = args
		self.session_id = 'logs,bm,%d,%s,%d,%s,%s,%d,%d,%d' % (int(time.time()), args.trace, args.nworker, args.src_nic,
			args.dest_nic + '.vtap' if args.macvtap else args.dest_nic, args.interval, args.swappiness, args.replay_speed)
		self.session_tmpdir = RUNNER_TMPDIR + '/' + self.session_id
		self.local_tmpdir = TESTER_TMPDIR + '/' + self.session_id

	def prework(self):
		self.init_test_session(self.session_id, self.local_tmpdir, self.session_tmpdir, self.args)

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
			'--enable-ps', '--ps-keywords', 'snort', '--ps-outfile', 'psstat.snort.csv'],
			cwd=self.session_tmpdir, store_pid=True, allow_error=True, stdout=sys.stdout.buffer, stderr=sys.stdout.buffer)
		self.snort_out = open(self.local_tmpdir + '/snort.out', 'wb')
		self.snort_proc = self.shell.spawn(['snort', '-A', 'fast', '-c', '/etc/snort/snort.conf', '-l', self.session_tmpdir, '-i', dest_nic],
			stdout=self.snort_out, stderr=self.snort_out, store_pid=True, allow_error=True)
		self.wait_for_snort(self.session_tmpdir)
		self.replay_trace(self.local_tmpdir, self.args.trace, self.args.nworker, self.args.src_nic, self.args.interval, self.args.replay_speed)
		self.snort_proc.send_signal(signal.SIGINT)
		snort_result = self.snort_proc.wait_for_result()
		log('snort returned with value %d.' % snort_result.return_code)
		self.snort_out.close()
		del self.snort_proc
		del self.snort_out
		self.sysmon_proc.send_signal(signal.SIGINT)
		self.sysmon_proc.wait_for_result()
		del self.sysmon_proc
		if self.status == self.STATUS_START:
			self.status = self.STATUS_DONE

	def postwork(self):
		log('Postwork...')
		if self.status == self.STATUS_DONE:
			self.upload_test_session(self.session_id, self.local_tmpdir, self.session_tmpdir)

	def cleanup(self):
		log('Cleaning up...')
		self.simple_call(['sudo', 'pkill', '-9', 'python'])
		if hasattr(self, 'sysmon_proc'):
			self.sysmon_proc.send_signal(signal.SIGKILL)
		if hasattr(self, 'snort_proc'):
			self.snort_proc.send_signal(signal.SIGKILL)
		if hasattr(self, 'snort_out'):
			self.snort_out.close()
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
	parser = argparse.ArgumentParser(description='Run snort directly on top of remote host and collect system info.')
	parser.add_argument('trace', type=str, help='Name of a trace file in trace repository.')
	parser.add_argument('nworker', type=int, help='Number of concurrent TCPreplay processes.')
	parser.add_argument('--src-nic', '-s', nargs='?', type=str, default='em2', help='Replay trace on this local NIC.')
	parser.add_argument('--dest-nic', '-d', nargs='?', type=str, default='em2', help='Trace will be observed on this NIC on the dest host.')
	parser.add_argument('--macvtap', '-v', default=False, action='store_true', help='If present, create a macvtap device on dest host.')
	parser.add_argument('--interval', '-t', nargs='?', type=int, default=4, help='Interval (sec) between collecting dest host info.')
	parser.add_argument('--swappiness', '-w', nargs='?', type=int, default=5, help='Memory swappiness of the host (e.g., 5).')
	parser.add_argument('--replay-speed', nargs='?', type=int, default=1, help='Speed of TCP replay (e.g., 2 for double the speed).')
	args = parser.parse_args()
	log(str(args))
	TestSnortBareMetal(args).start()


if __name__ == '__main__':
	main()
