#!/usr/bin/python3

import os
import signal
import sys

from testbase import *


class TestSuricataBase:

	MACVTAP_NAME = 'macvtap0'
	ETHTOOL_ARGS = ('tso', 'gro', 'lro', 'gso', 'rx', 'tx', 'sg')
	STATUS_INIT = 0
	STATUS_START = 1
	STATUS_DONE = 2
	STATUS_ABORT = 3

	def __init__(self):
		self.status = self.STATUS_INIT
		reboot_remote_host(host=RUNNER_HOST, user=RUNNER_USER)
		self.shell = get_remote_shell(host=RUNNER_HOST, user=RUNNER_USER)

	def simple_call(self, cmd):
		return self.shell.run(cmd, stdout=sys.stdout.buffer, stderr=sys.stdout.buffer, allow_error=True).return_code

	def init_test_session(self, session_id, local_tmpdir, session_tmpdir, args):
		log('Adjusting swappiness of remote host...')
		self.simple_call(['sudo', 'sysctl', '-w', 'vm.swappiness=' + str(args.swappiness)])
		self.simple_call(['sysctl', 'vm.swappiness'])
		log('Creating local temp dir...')
		subprocess.call(['mkdir', '-p', local_tmpdir])
		subprocess.call(['sudo', 'pkill', '-9', 'tcpreplay'])
		log('Initializing remote temp dir...')
		self.simple_call(['mkdir', '-p', session_tmpdir])
		subprocess.call(['rsync', '-zvrpE', './tester_script', '%s@%s:%s/' % (RUNNER_USER, RUNNER_HOST, RUNNER_TMPDIR)])
		log('Making sure remote system is clean...')
		self.simple_call(['sudo', 'ip', 'link', 'del', 'macvtap0'])
		self.simple_call(['sudo', 'pkill', '-9', 'Suricata-Main'])
		# self.simple_call(['sudo', 'pkill', '-9', 'top'])
		# self.simple_call(['sudo', 'pkill', '-9', 'atop'])
		# Configure NIC to fit Suricata's need.
		log('Configuring src and dest NICs...')
		self.simple_call(['sudo', 'ifconfig', args.dest_nic, 'promisc'])
		for optarg in self.ETHTOOL_ARGS:
			subprocess.call(['sudo', 'ethtool', '-K', args.src_nic, optarg, 'off'])
			self.simple_call(['sudo', 'ethtool', '-K', args.dest_nic, optarg, 'off'])
		# Setup macvtap
		if args.macvtap is True:
			log('Creating macvtap device for NIC "%s"...' % args.dest_nic)
			tap_name = self.MACVTAP_NAME
			mac_addr = gen_random_mac_addr()
			self.simple_call(['sudo', 'ip', 'link', 'add', 'link', args.dest_nic, 'name', tap_name, 'type', 'macvtap', 'mode', 'passthru'])
			self.simple_call(['sudo', 'ip', 'link', 'set', tap_name, 'address', mac_addr, 'up'])
			self.simple_call(['sudo', 'ip', 'link', 'show', tap_name])

	def upload_test_session(self, session_id, local_tmpdir, session_tmpdir):
		log('Upload session data to data server...')
		data_store = '%s@%s:%s/' % (DATA_USER, DATA_HOST, DATA_DIR)
		subprocess.call(['sudo', 'rsync', '-zvrpE', local_tmpdir, data_store])
		self.simple_call(['sudo', 'rsync', '-zvrpE', session_tmpdir, data_store])

	def destroy_session(self, session_id, local_tmpdir, session_tmpdir, args):
		subprocess.call(['sudo', 'pkill', '-9', 'tcpreplay'])
		if args.macvtap:
			self.simple_call(['sudo', 'ip', 'link', 'del', 'macvtap0'])
		subprocess.call(['rm', '-rfv', local_tmpdir])
		self.simple_call(['rm', '-rfv', session_tmpdir])

	def close(self):
		del self.shell

	def wait_for_suricata(self, session_tmpdir, prepend=[]):
		while True:
			ret = self.shell.run(prepend + ['test', '-f', session_tmpdir + '/eve.json'], allow_error=True)
			if ret.return_code != 0:
				log('Waiting for 8sec for Suricata to stabilize...')
				time.sleep(8)
			else:
				log('Suricata is ready.')
				return

	def replay_trace(self, local_tmpdir, trace_file, nworker, src_nic, poll_interval_sec, replay_speed_X):
		monitor_proc = subprocess.Popen([os.getcwd() + '/tester_script/sysmon.py',
			'--delay', str(poll_interval_sec), '--outfile', 'sysstat.sender.csv',
			'--nic', src_nic, '--nic-outfile', 'netstat.tcpreplay.{nic}.csv'],
			stdout=sys.stdout, stderr=sys.stderr, cwd=local_tmpdir)
		workers = []
		with open(local_tmpdir + '/tcpreplay.out', 'wb') as f:
			try:
				cmd = ['sudo', 'tcpreplay', '-i', src_nic, LOCAL_TRACE_REPO_DIR + '/' + trace_file]
				if replay_speed_X != 1:
					cmd += ['--multiplier', str(replay_speed_X)]
				for i in range(nworker):
					workers.append(subprocess.Popen(cmd, stdout=f, stderr=f))
				log('Waiting for all %d tcpreplay processes to complete...' % nworker)
				for w in workers:
					w.wait()
				log('All tcpreplay processes are complete. Wait for 20sec before proceeding.')
				time.sleep(20)
			except KeyboardInterrupt as e:
				log('Interrupted. Stopping tcpreplay processes...')
				for w in workers:
					w.terminate()
				self.status = self.STATUS_ABORT
				log('Aborted.')
			finally:
				monitor_proc.send_signal(signal.SIGINT)
				monitor_proc.wait()

	def start(self):
		raise NotImplementedError()
