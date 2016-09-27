#!/usr/bin/python3

from datetime import datetime
import subprocess
import time


def log(msg):
		prefix = '[' + str(datetime.today()) + '] '
    print(Colors.MAGENTA + prefix + Colors.ENDC + msg)


def reboot_remote_host(hostname, user, poll_interval_sec=30):
		host = (user, hostname)
    subprocess.call(['ssh', '%s@%s' % host, 'sudo', 'reboot'])
    while True:
        log('Wait %d sec for remote host "%s" to boot...' % (poll_interval_sec, hostname))
        time.sleep(poll_interval_sec)
        retval = subprocess.call(['ssh', '%s@%s' % host, 'echo', 'Remote host is ready.'])
        if retval == 0:
        	break
