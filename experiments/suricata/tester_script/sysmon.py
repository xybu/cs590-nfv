#!/usr/bin/python3

"""
sysmon.py

System monitor.

Monitor system wide resource usage and availability.

@author	Xiangyu Bu <bu1@purdue.edu>
"""

import argparse
import os
import sys
import threading
import time
import psutil


proceed = True


def monitor_system_res(delay_sec, prefix, suffix):
	print('System monitor started.', file=sys.stderr)
	base_timestamp = int(time.time())
	ncores = psutil.cpu_count()
	with open(prefix + 'sysstat' + suffix + '.csv', 'w') as f:
		f.write('Timestamp,  Uptime, NCPU, %CPU, ' + ', '.join(['%CPU' + str(i) for i in range(ncores)]) +
			', %MEM, mem.total.KB, mem.used.KB, mem.avail.KB, mem.free.KB' +
			', %SWAP, swap.total.KB, swap.used.KB, swap.free.KB' +
			', io.read, io.write, io.read.KB, io.write.KB, io.read.ms, io.write.ms\n')
		prev_disk_stat = psutil.disk_io_counters()
		last_timestamp = int(time.time())
		while proceed:
			# Process timestamp
			timestamp = int(time.time())
			uptime = timestamp - base_timestamp
			# Process CPU usage in percentage.
			# Assuming the number of CPUs do not change throughout execution.
			# ncores = psutil.cpu_count()
			total_cpu_percent = psutil.cpu_percent(percpu=False)
			percpu_percent = psutil.cpu_percent(percpu=True)
			# Process memory usage.
			mem_stat = psutil.virtual_memory()
			swap_stat = psutil.swap_memory()
			# Process Disk usage.
			disk_stat = psutil.disk_io_counters()
			line = str(timestamp) + ', ' + str(uptime) + ', ' + str(ncores) + ', ' + str(total_cpu_percent*ncores) + ', '
			line += ', '.join([str(i) for i in percpu_percent])
			line += ', ' + str(mem_stat.percent) + ', ' + str(mem_stat.total >> 10) + ', ' + str(mem_stat.used >> 10) + ', ' + str(mem_stat.available >> 10) + ', ' + str(mem_stat.free >> 10)
			line += ', ' + str(swap_stat.percent) + ', ' + str(swap_stat.total >> 10) + ', ' + str(swap_stat.used >> 10) + ', ' + str(swap_stat.free >> 10)
			line += ', ' + str(disk_stat.read_count - prev_disk_stat.read_count) + ', ' + str(disk_stat.write_count - prev_disk_stat.write_count) + \
				', ' + str((disk_stat.read_bytes - prev_disk_stat.read_bytes) >> 10) + ', ' + str((disk_stat.write_bytes - prev_disk_stat.write_bytes) >> 10) + \
				', ' + str(disk_stat.read_time - prev_disk_stat.read_time) + ', ' + str(disk_stat.write_time - prev_disk_stat.write_time)
			f.write(line + '\n')
			prev_disk_stat = disk_stat
			# Deal with timestamp drifting.
			d = delay_sec + delay_sec - timestamp + last_timestamp
			if d <= 0:
				d = delay_sec >> 1
			time.sleep(d)
			last_timestamp = timestamp
	print('System monitor stopped.', file=sys.stderr)


def monitor_nerwork_usage(delay_sec, nics, prefix, suffix):
	"""
	Values are increments during the interval to observe.
	"""
	print('Network monitor started.', file=sys.stderr)
	base_timestamp = int(time.time())
	all_nics = psutil.net_if_stats()
	nics = {k: open(prefix + 'netstat.' + k + suffix + '.csv', 'w') for k in nics.split(',') if k in all_nics}
	nics['host'] = open('netstat.csv', 'w')
	for nic, f in nics.items():
		f.write('Timestamp,  Uptime, NIC, bytes_sent, bytes_recv, packets_sent, packets_recv, errin, errout, dropin, dropout\n')
	last_stat = psutil.net_io_counters(pernic=True)
	last_stat['host'] = psutil.net_io_counters()
	last_timestamp = int(time.time())
	while proceed:
		# Process timestamp
		timestamp = int(time.time())
		uptime = timestamp - base_timestamp
		net_stat = psutil.net_io_counters(pernic=True)
		net_stat['host'] = psutil.net_io_counters()
		for nic, f in nics.items():
			stat = net_stat[nic]
			prevstat = last_stat[nic]
			f.write(str(timestamp) + ', ' + str(uptime) + ', ' + nic + ', ' + \
				str(stat.bytes_sent-prevstat.bytes_sent) + ', ' + str(stat.bytes_recv-prevstat.bytes_recv) + ', ' + \
				str(stat.packets_sent-prevstat.packets_sent) + ', ' + str(stat.packets_recv-prevstat.packets_recv) + ', ' + \
				str(stat.errin-prevstat.errin) + ', ' + str(stat.errout-prevstat.errout) + ', ' + str(stat.dropin-prevstat.dropin) + ', ' + str(stat.dropout-prevstat.dropout) + '\n')
		last_stat = net_stat
		d = delay_sec + delay_sec - timestamp + last_timestamp
		if d <= 0:
			d = delay_sec >> 1
		time.sleep(d)
		last_timestamp = timestamp
	for nic, f in nics.items():
		f.close()
	print('System monitor stopped.', file=sys.stderr)


def main():
	try:
		parser = argparse.ArgumentParser(description='Monitor system-wide resource availability.')
		parser.add_argument('--delay', '-d', type=int, default=4, required=True, help='Interval, in sec, to poll information.')
		parser.add_argument('--nic', '-n', type=str, nargs='?', default=None, required=False, help='Specify particular NICs, separated by a comma, to monitor. Default is none.')
		parser.add_argument('--prefix', '-p', type=str, nargs='?', default='', required=False, help='String to prepend to output file name. Default: "".')
		parser.add_argument('--suffix', '-s', type=str, nargs='?', default='', required=False, help='String to append to output file name before ext name. Default: "".')
		args = parser.parse_args()
		try:
			psutil.Process(os.getpid()).nice(-20)
		except:
			print('Error: failed to elevate priority!', file=sys.stderr)
		sysstat_thread = threading.Thread(target=monitor_system_res, args=(args.delay, args.prefix, args.suffix))
		sysstat_thread.start()
		if args.nic is not None:
			netstat_thread = threading.Thread(target=monitor_nerwork_usage, args=(args.delay, args.nic, args.prefix, args.suffix))
			netstat_thread.start()
		while True:
			time.sleep(3600)
	except KeyboardInterrupt:
		global proceed
		proceed = False
		sysstat_thread.join()
		if args.nic is not None:
			netstat_thread.join()


if __name__ == '__main__':
	main()
