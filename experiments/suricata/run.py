#!/usr/bin/python3

import os
import subprocess
import sys
from helpers import *


def do_command(line):
	line = line.split(maxsplit=2)
	nround = int(line[0])
	script = line[1]
	args = line[2].split() if len(line) == 3 else []
	command = ['sudo', script] + args
	for i in range(0, nround):
		log('Round %d / %d: ' % (i+1, nround) + str(command))
		subprocess.call(command)


def do_all_commands(test_path):
	with open(test_path, 'r') as f:
		for line in f:
			line = line.strip()
			if len(line) == 0 or line.startswith('#'):
				continue
			else:
				do_command(line)
	log('All commands are done.')


def main():
	do_all_commands('./config/tests.%s.txt' % HOSTNAME)


if __name__ == '__main__':
	main()
