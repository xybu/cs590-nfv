#!/usr/bin/python3

import os
import signal
import subprocess
import sys
import time

import bc_utils


class BenchmarkBase:
    STATUS_INIT = 0
    STATUS_START = 1
    STATUS_DONE = 2
    STATUS_ABORTED = 3

    SENDER_SYSMON_OUTFILE = 'sysstat.sender.csv'
    SENDER_SYSMON_NIC_OUTFILE = 'netstat.tcpreplay.{nic}.csv'
    SENDER_TCPREPLAY_OUTFILE = 'tcpreplay.out'

    ETHTOOL_ARGS = ('tso', 'gro', 'lro', 'gso', 'rx', 'tx', 'sg')

    def __init__(self):
        pass

    def init_session(self, hostname, user,
                     reboot=False, reboot_poll_interval_sec=30,
                     remote_pkill_list=None, local_pkill_list=None,
                     remote_tmpdir='/tmp/benchmark', local_tmpdir='/tmp/benchmark',
                     remote_vm_swappiness=5):
        self.status = self.STATUS_INIT
        self.remote_hostname = hostname
        self.remote_user = user
        self.remote_tmpdir = remote_tmpdir
        self.local_tmpdir = local_tmpdir
        if reboot:
            bc_utils.reboot_remote_host(hostname=hostname, user=user, poll_interval_sec=reboot_poll_interval_sec)
        self.shell = bc_utils.get_remote_shell(host=hostname, user=user)
        # Clean up residual processes if any.
        if isinstance(local_pkill_list, list):
            for proc_name in local_pkill_list:
                self.local_call(['sudo', 'pkill', '-9', proc_name])
        if isinstance(remote_pkill_list, list):
            for proc_name in remote_pkill_list:
                self.remote_call(['sudo', 'pkill', '-9', proc_name])
        # Adjust swappiness of remote host.
        bc_utils.log('Adjusting vm.swappiness of remote host...')
        self.remote_call(['sudo', 'sysctl', '-w', 'vm.swappiness=' + str(remote_vm_swappiness)])
        self.remote_call(['sysctl', 'vm.swappiness'])
        # Create temp dir on both hosts.
        self.remote_call(['sudo', 'rm', '-rfv', remote_tmpdir])
        self.remote_call(['sudo', 'mkdir', '-p', remote_tmpdir])
        self.local_call(['sudo', 'rm', '-rfv', local_tmpdir])
        self.local_call(['sudo', 'mkdir', '-p', local_tmpdir])

    def upload_session(self, ds_hostname, ds_user, ds_path):
        bc_utils.log('Upload session data to data server...')
        data_store = '%s@%s:%s/' % (ds_user, ds_hostname, ds_path)
        self.local_call(['sudo', 'rsync', '-zrvpE', self.local_tmpdir, data_store])
        self.remote_call(['sudo', 'rsync', '-zrvpE', self.remote_tmpdir, data_store])

    def destroy_session(self):
        self.local_call(['sudo', 'pkill', '-9', 'tcpreplay'])
        self.local_call(['sudo', 'rm', '-rfv', self.local_tmpdir])
        self.remote_call(['sudo', 'rm', '-rfv', self.remote_tmpdir])
        del self.shell

    def local_call(self, *args, **kwargs):
        return subprocess.call(*args, **kwargs)

    def remote_call(self, cmd):
        return self.shell.run(cmd, stdout=sys.stdout.buffer, stderr=sys.stdout.buffer, allow_error=True).return_code

    def copy_to_remote(self, paths):
        for tup in paths:
            f, t = tup
            self.local_call(['sudo', 'rsync', '-zrvpE', f, '%s@%s:/%s' % (self.remote_user, self.remote_hostname, t)])

    def turn_off_nic_opts(self, nic, is_remote=True, prepend_cmdargs=None):
        if prepend_cmdargs is None:
            prepend_cmdargs = []
        if is_remote:
            for opt in self.ETHTOOL_ARGS:
                self.remote_call(prepend_cmdargs + ['sudo', 'ethtool', '-K', nic, opt, 'off'])
        else:
            for opt in self.ETHTOOL_ARGS:
                self.local_call(prepend_cmdargs + ['sudo', 'ethtool', '-K', nic, opt, 'off'])

    def remote_add_macvtap(self, tap_name, nic_name):
        bc_utils.log('Creating macvtap device "%s" for NIC "%s" in remote host...' % (tap_name, nic_name))
        self.remote_del_macvtap(tap_name)
        self.remote_call(
            ['sudo', 'ip', 'link', 'add', 'link', nic_name, 'name', tap_name, 'type', 'macvtap', 'mode', 'passthru'])
        self.remote_call(['sudo', 'ip', 'link', 'set', tap_name, 'address', bc_utils.gen_random_mac_addr(), 'up'])
        self.remote_call(['sudo', 'ip', 'link', 'show', tap_name])

    def remote_del_macvtap(self, tap_name):
        self.remote_call(['sudo', 'ip', 'link', 'del', tap_name])

    def replay_trace(self, trace_filepath, src_nic, nworkers, replay_speed_multiplier=1.0,
                     replay_finish_pause_sec=10, sysmon_poll_interval_sec=4):
        monitor_proc = subprocess.Popen(
            [os.path.dirname(os.path.abspath(__file__)) + '/sysmon.py',
             '--delay', str(sysmon_poll_interval_sec),
             '--outfile', self.SENDER_SYSMON_OUTFILE,
             '--nic', src_nic, '--nic-outfile', self.SENDER_SYSMON_NIC_OUTFILE],
            stdout=sys.stdout, stderr=sys.stderr, cwd=self.local_tmpdir)
        workers = []
        with open(self.local_tmpdir + '/' + self.SENDER_TCPREPLAY_OUTFILE, 'wb') as f:
            try:
                cmd = ['sudo', 'tcpreplay', '-i', src_nic, trace_filepath]
                if replay_speed_multiplier != 1.0:
                    cmd += ['--multiplier', str(replay_speed_multiplier)]
                for i in range(nworkers):
                    workers.append(subprocess.Popen(cmd, stdout=f, stderr=f))
                bc_utils.log('Waiting for all %d tcpreplay processes to complete...' % nworkers)
                for w in workers:
                    w.wait()
                bc_utils.log('All tcpreplay processes finished. Pause for %d sec.' % replay_finish_pause_sec)
                time.sleep(replay_finish_pause_sec)
            except KeyboardInterrupt:
                bc_utils.log('Interrupted. Stopping tcpreplay processes...')
                for w in workers:
                    w.terminate()
                self.status = self.STATUS_ABORTED
                self.local_call(['sudo', 'pkill', '-9', 'tcpreplay'])
                bc_utils.log('Aborted.')
            finally:
                monitor_proc.send_signal(signal.SIGINT)
                monitor_proc.wait()
