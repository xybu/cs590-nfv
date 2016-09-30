#!/usr/bin/python3

from colors import Colors
from datetime import datetime
import random
import spur
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
        ret = subprocess.call(['ssh', '%s@%s' % host, 'echo', 'Remote host is ready.'])
        if ret == 0:
            break


def get_remote_shell(host, user):
    log('Establishing SSH to "%s@%s"...' % (user, host))
    return spur.SshShell(hostname=host, username=user,
		missing_host_key=spur.ssh.MissingHostKey.accept,
		load_system_host_keys=True,
		look_for_private_keys=True)


def gen_random_mac_addr():
    return "52:54:00:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
