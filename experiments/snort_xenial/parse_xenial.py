#!/usr/bin/python3

import csv
import concurrent.futures
import json
import os
import sys
import multiprocessing
import threading
import traceback

from colors import Colors
from dataparser import mon
from dataparser import exceptions
from dataparser import snort_parser
from dataparser import snort_collection

snortcollections = dict()
netstatcollections = dict()
sysstatcollections = dict()
psstatcollections = dict()
snortparser = snort_parser.SnortOutputParser()
sysstatparser = mon.SysStatParser()
netstatparser = mon.NetStatParser()
psstatparser = mon.PsStatParser()

# The number of concurrent workers equals the number of CPU threads.
NUM_WORKERS = multiprocessing.cpu_count() 


def get_all_logdirs(path, depth=2):
	if depth == 1:
		print('Adding all "logs.*"" dirs under "%s".' % path)
		return sorted([path + '/' + i for i in os.listdir(path) if i.startswith('logs') and os.path.isdir(path + '/' + i)])
	all_logdirs = []
	for name in os.listdir(path):
		if os.path.isdir(path + '/' + name):
			all_logdirs += get_all_logdirs(path + '/' + name, depth=depth-1)
	return all_logdirs


_collection_lock = threading.Lock()

_task_count_lock = threading.Lock()
task_count = dict()


def get_collection(collections, name, default_class):
	_collection_lock.acquire()
	if name not in collections:
		c = collections[name] = default_class(name)
	else:
		c = collections[name]
	_collection_lock.release()
	return c


def get_collection_name(engine, ts, trace, nworker, args):
	return ','.join([engine, trace, nworker, args])


def _parse_csvstat(collections, cls, parser, path, engine, ts, trace, nworker, args):
	if os.path.isfile(path):
		thname = threading.current_thread().name
		if thname not in task_count:
			_task_count_lock.acquire()
			task_count[thname] = 1
			_task_count_lock.release()
		else:
			task_count[thname] += 1
		print('\033[93m[%s]\033[0m Start "%s" (%d).' % (thname, path, task_count[thname]))
		name = get_collection_name(engine, ts, trace, nworker, args)
		col = get_collection(collections, name, cls)
		try:
			id = col.get_key(engine, ts, trace, nworker, args)
			data = parser.parse(path)
			col.add(id, data)
		except exceptions.NoContentException as ex:
			print('Error: ' + str(ex))
		print('\033[92m[%s]\033[0m Done "%s" (%d).' % (thname, path, task_count[thname]))


def parse_netstat(path, engine, ts, trace, nworker, args):
	_parse_csvstat(netstatcollections, mon.NetStatCollection, netstatparser,
		path, engine, ts, trace, nworker, args)


def parse_sysstat(path, engine, ts, trace, nworker, args):
	_parse_csvstat(sysstatcollections, mon.SysStatCollection, sysstatparser,
		path, engine, ts, trace, nworker, args)


def parse_psstat(path, engine, ts, trace, nworker, args):
	_parse_csvstat(psstatcollections, mon.PsStatCollection, psstatparser,
		path, engine, ts, trace, nworker, args)


def parse_snort(path, engine, ts, trace, nworker, args):
	_parse_csvstat(snortcollections, snort_collection.SnortOutCollection, snortparser,
		path, engine, ts, trace, nworker, args)


def execute(all_futures, executor, func, *args):
	print('\033[94m[%s]\033[0m Adding Task %d - "%s"...' % (threading.current_thread().name, len(all_futures), args[0]))
	all_futures.add(executor.submit(func, *args))


def traverse_logdir(path, scan_depth):
	num_successes = 0
	errors = []
	all_logdirs = get_all_logdirs(path, scan_depth)
	all_futures = set()
	print('INFO: using %d concurrent workers to parse %d log dirs.' % (NUM_WORKERS * 2, len(all_logdirs)))
	with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS * 2) as executor:
		for dirpath in all_logdirs:
			parent, dirname = os.path.split(dirpath)
			prefix, engine, ts, trace, nworker, args = dirname.split(',', maxsplit=5)
			args = args.replace(',1024m,', ',1g,', 1)
			execute(all_futures, executor, parse_snort, dirpath + '/snort.out', engine, ts, trace, nworker, args)
			execute(all_futures, executor, parse_sysstat, dirpath + '/sysstat.sender.csv', engine, ts, trace, nworker, args + ',sender')
			execute(all_futures, executor, parse_netstat, dirpath + '/netstat.tcpreplay.enp34s0.csv', engine, ts, trace, nworker, args + ',netout')
			execute(all_futures, executor, parse_netstat, dirpath + '/netstat.enp34s0.csv', engine, ts, trace, nworker, args + ',netin')
			execute(all_futures, executor, parse_sysstat, dirpath + '/sysstat.receiver.csv', engine, ts, trace, nworker, args + ',receiver')
			if prefix == 'bm':
				execute(all_futures, executor, parse_psstat, dirpath + '/psstat.snort.csv', engine, ts, trace, nworker, args)
			elif prefix == 'docker':
				execute(all_futures, executor, parse_psstat, dirpath + '/psstat.docker.csv', engine, ts, trace, nworker, args)
			elif engine == 'vm':
				execute(all_futures, executor, parse_psstat, dirpath + '/psstat.qemu.csv', engine, ts, trace, nworker, args)
				execute(all_futures, executor, parse_sysstat, dirpath + '/sysstat.vm.csv', engine, ts, trace, nworker, args + ',vm')
				execute(all_futures, executor, parse_psstat, dirpath + '/psstat.snort.vm.csv', engine, ts, trace, nworker, args + ',vm,snort')
				execute(all_futures, executor, parse_netstat, dirpath + '/netstat.ens4.vm.csv', engine, ts, trace, nworker, args + ',vm,netin')
				execute(all_futures, executor, parse_netstat, dirpath + '/netstat.ens9.vm.csv', engine, ts, trace, nworker, args + ',vm,netin')
		print('\033[94m[%s]\033[0m \033[92mWaiting for all tasks to complete.\033[0m' % threading.current_thread().name)
		for future in concurrent.futures.as_completed(all_futures):
			try:
				future.result()
				num_successes += 1
			except Exception as e:
				errors.append((future, str(e)))
				print(Colors.RED + 'Error: %s' % e + Colors.ENDC)
				print(traceback.format_exc())
	print(Colors.GRAY + '-' * 80 + Colors.ENDC)
	print(Colors.CYAN + 'Summary:' + Colors.ENDC)
	print(Colors.GREEN + 'Successes:\t%d' % num_successes + Colors.ENDC)
	print(Colors.RED + 'Failures:\t%d' % len(errors) + Colors.ENDC)
	for e in sorted(errors):
	    print(Colors.RED + '|- %s: %s' % e + Colors.ENDC)


def main():
	data_dir = sys.argv[1]
	output_dir = sys.argv[2]
	scan_depth = int(sys.argv[3])
	try:
		os.makedirs(output_dir)
		output_dir = os.path.abspath(output_dir)
	except OSError as e:
		if e.errno != 17:
			print('Error: cannot create output path "%s": %s.' % (output_dir, str(e)))
			return 1
		else:
			output_dir = os.path.abspath(output_dir)
	try:
		os.chdir(data_dir)
	except Exception as e:
		print('Error: cannot chdir to path "%s": %s.' % (data_dir, str(e)))
		return 1		
	
	traverse_logdir('.', scan_depth)

	try:
		os.chdir(output_dir)
	except Exception as e:
		print('Error: cannot chdir to path "%s": %s. Use pwd ("%s") instead.' % (output_dir, str(e), os.getcwd()))
	with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS * 2) as executor:
		futures = set()
		for col in (snortcollections, netstatcollections, sysstatcollections, psstatcollections):
			for name, collection in col.items():
				futures.add(executor.submit(collection.to_xlsx))
		for future in concurrent.futures.as_completed(futures):
			try:
				future.result()
			except Exception as e:
				print(Colors.RED + 'Error: %s' % e + Colors.ENDC)
				print(traceback.format_exc())
	
	os.system("grep -r 'Sample size' | sort | tee 'sample_size.txt'")


if __name__ == '__main__':
	main()
