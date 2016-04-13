import random
import subprocess
import time

import spur
from helpers import *


def reboot_remote_host(host, user):
	log('Rebooting host "%s"...' % host)
	retval = subprocess.call(['ssh', '%s@%s' % (user, host), 'sudo', 'reboot'])
	retval = 1
	while retval != 0:
		log('Wait 30sec for remote host "%s" to start...' % host)
		time.sleep(30)
		retval = subprocess.call(['ssh', '%s@%s' % (user, host), 'echo', 'Remote host is ready.'])


def get_remote_shell(host=RUNNER_HOST, user=RUNNER_USER):
	log('Obtaining SSH to "%s@%s"...' % (user, host))
	return spur.SshShell(hostname=host, username=user, 
		missing_host_key=spur.ssh.MissingHostKey.accept,
		load_system_host_keys=True,
		look_for_private_keys=True)


def gen_random_mac_addr():
	return "52:54:00:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
