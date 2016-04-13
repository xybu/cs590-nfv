#!/usr/bin/python3

"""
psmon.py

Process Set monitor.

Monitor resource usage of a subset of living processes. For example, if keyword
"docker" is given, then it reports, every T seconds, the sum of resource (CPU,
RSS, IO, CtxSw, NThreads) usage of all processes whose name contains "docker"
their children processes.

@author	Xiangyu Bu <bu1@purdue.edu>
"""

import argparse
import os
import sys
import time

import psutil


def stat_proc(proc, stat, visited=set()):
	""" Recursively stat a process and its children processes. """
	if proc.pid in visited:
		return
	# print('Visiting process %d.' % proc.pid)
	visited.add(proc.pid)
	io = proc.io_counters()
	mem_rss = proc.memory_info().rss
	mem_percent = proc.memory_percent('rss')
	nctxsw = proc.num_ctx_switches()
	nctxsw = nctxsw.voluntary + nctxsw.involuntary
	nthreads = proc.num_threads()
	cpu_percent = proc.cpu_percent()
	stat['io.read'] += io.read_count
	stat['io.write'] += io.write_count
	stat['io.read.KB'] += io.read_bytes >> 10
	stat['io.write.KB'] += io.write_bytes >> 10
	stat['mem.rss.KB'] += mem_rss >> 10
	stat['%MEM'] += mem_percent
	stat['nctxsw'] += nctxsw
	stat['nthreads'] += nthreads
	stat['%CPU'] += cpu_percent
	for c in proc.children():
		stat_proc(c, stat, visited)


def poll_stat(keywords, pids, delay_sec, out):
	base_stat = {
		'io.read': 0,
		'io.write': 0,
		'io.read.KB': 0,
		'io.write.KB': 0,
		'mem.rss.KB': 0,
		'%MEM': 0,
		'%CPU': 0,
		'nctxsw': 0,
		'nthreads': 0
	}
	prev_stat = dict(base_stat)
	keys = sorted(base_stat.keys())
	out.write('Timestamp, Uptime, ' + ', '.join(keys) + '\n')
	base_timestamp = int(time.time())
	last_timestamp = int(time.time())
	while True:
		visited = set()
		curr_stat = dict(base_stat)
		timestamp = int(time.time())
		uptime = timestamp - base_timestamp
		for proc in psutil.process_iter():
			try:
				pinfo = proc.as_dict(attrs=['pid', 'name'])
			except psutil.NoSuchProcess:
				pass
			else:
				if pinfo['pid'] in visited:
					continue
				if pinfo['pid'] in pids:
					stat_proc(proc, curr_stat, visited)
				else:
					for k in keywords:
						if k in pinfo['name'].lower():
							stat_proc(proc, curr_stat, visited)
							break
		curr_stat['%CPU'] = round(curr_stat['%CPU'], 3)
		curr_stat['%MEM'] = round(curr_stat['%MEM'], 3)
		line = str(timestamp) + ', ' + str(uptime) + ', '
		line += ', '.join([str(curr_stat[k]) for k in keys])
		out.write(line + '\n')
		prev_stat = curr_stat
		d = delay_sec + delay_sec - timestamp + last_timestamp
		if d <= 0:
			d = delay_sec >> 1
		time.sleep(d)
		last_timestamp = timestamp


def main():
	parser = argparse.ArgumentParser(description='Calculate sum of resource usage of a set of processes and their children.')
	parser.add_argument('--keywords', '-k', nargs='*', type=str, help='Include processes whose name contains the keyword.')
	parser.add_argument('--pids', '-p', nargs='*', type=int, help='Include the specified PIDs.')
	parser.add_argument('--delay', '-d', nargs='?', type=int, default=4, help='Interval, in sec, between two polls.')
	parser.add_argument('--out', '-o', nargs='?', type=str, help='Save output to the specified file.')
	args = parser.parse_args()
	print(args)
	if args.pids is None:
		args.pids = set()
	else:
		args.pids = set(args.pids)
	if args.keywords is None:
		args.keywords = []
	else:
		# Convert to lowercase to achieve case Insensitiveness.
		keywords = [k.lower() for k in args.keywords]
		args.keywords = keywords
	try:
		psutil.Process(os.getpid()).nice(-20)
	except:
		print('Error: failed to elevate priority!', file=sys.stderr)
	try:
		if args.out is not None:
			with open(args.out, 'w') as f:
				poll_stat(args.keywords, args.pids, args.delay, f)
		else:
			poll_stat(args.keywords, args.pids, args.delay, sys.stdout)
	except KeyboardInterrupt:
		pass


if __name__ == '__main__':
	main()
