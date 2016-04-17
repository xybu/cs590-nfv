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
from dataparser import eve
from dataparser import mon
from dataparser import exceptions


DATA_VALUT_DIR = "/scratch/bu1/suricataV4"

evecollections = dict()
netstatcollections = dict()
sysstatcollections = dict()
psstatcollections = dict()
eveparser = eve.EveParser()
sysstatparser = mon.SysStatParser()
netstatparser = mon.NetStatParser()
psstatparser = mon.PsStatParser()

# The number of concurrent workers equals the number of CPU threads.
NUM_WORKERS = multiprocessing.cpu_count() 


def get_all_logdirs(path):
	all_logdirs = sorted([i for i in os.listdir(path) if i.startswith('logs')])
	return all_logdirs


_collection_lock = threading.Lock()


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
		print('Processing "%s"...' % path)
		name = get_collection_name(engine, ts, trace, nworker, args)
		col = get_collection(collections, name, cls)
		try:
			id = col.get_key(engine, ts, trace, nworker, args)
			data = parser.parse(path)
			col.add(id, data)
		except exceptions.NoContentException as ex:
			print('Error: ' + str(ex))


def parse_netstat(path, engine, ts, trace, nworker, args):
	_parse_csvstat(netstatcollections, mon.NetStatCollection, netstatparser,
		path, engine, ts, trace, nworker, args)


def parse_sysstat(path, engine, ts, trace, nworker, args):
	_parse_csvstat(sysstatcollections, mon.SysStatCollection, sysstatparser,
		path, engine, ts, trace, nworker, args)


def parse_psstat(path, engine, ts, trace, nworker, args):
	_parse_csvstat(psstatcollections, mon.PsStatCollection, psstatparser,
		path, engine, ts, trace, nworker, args)


def parse_eve(path, engine, ts, trace, nworker, args):
	_parse_csvstat(evecollections, eve.EveCollection, eveparser,
		path, engine, ts, trace, nworker, args)


def execute(all_futures, executor, func, *args):
	all_futures.add(executor.submit(func, *args))


def traverse_logdir(path):
	num_successes = 0
	errors = []
	all_logdirs = get_all_logdirs(path)
	all_futures = set()
	print('INFO: using %d concurrent workers to parse %d log dirs.' % (NUM_WORKERS, len(all_logdirs)))
	with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS * 2) as executor:
		for dirname in all_logdirs:
			prefix, engine, ts, trace, nworker, args = dirname.split(',', maxsplit=5)
			parent_path = path + '/' + dirname
			execute(all_futures, executor, parse_eve, parent_path + '/eve.json', engine, ts, trace, nworker, args)
			execute(all_futures, executor, parse_sysstat, parent_path + '/sysstat.sender.csv', engine, ts, trace, nworker, args + ',sender')
			execute(all_futures, executor, parse_netstat, parent_path + '/netstat.tcpreplay.em2.csv', engine, ts, trace, nworker, args + ',netout')
			execute(all_futures, executor, parse_netstat, parent_path + '/netstat.enp34s0.csv', engine, ts, trace, nworker, args + ',netin')
			execute(all_futures, executor, parse_sysstat, parent_path + '/sysstat.receiver.csv', engine, ts, trace, nworker, args + ',receiver')
			if prefix == 'bm':
				execute(all_futures, executor, parse_psstat, parent_path + '/psstat.suricata.csv', engine, ts, trace, nworker, args)
			elif prefix == 'docker':
				execute(all_futures, executor, parse_psstat, parent_path + '/psstat.docker.csv', engine, ts, trace, nworker, args)
			elif engine == 'vm':
				execute(all_futures, executor, parse_psstat, parent_path + '/psstat.qemu.csv', engine, ts, trace, nworker, args)
				execute(all_futures, executor, parse_sysstat, parent_path + '/sysstat.vm.csv', engine, ts, trace, nworker, args + ',vm')
				execute(all_futures, executor, parse_psstat, parent_path + '/psstat.suricata.vm.csv', engine, ts, trace, nworker, args + ',vm,suricata')
				execute(all_futures, executor, parse_netstat, parent_path + '/netstat.eth1.vm.csv', engine, ts, trace, nworker, args + ',vm,netin')
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
	try:
		os.mkdir('data')
		os.chdir('data')
		print(os.getcwd())
	except:
		pass
	traverse_logdir(DATA_VALUT_DIR)
	with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS * 2) as executor:
		futures = set()
		for col in (evecollections, netstatcollections, sysstatcollections, psstatcollections):
			for name, collection in col.items():
				futures.add(executor.submit(collection.to_xlsx))
		for future in concurrent.futures.as_completed(futures):
			try:
				future.result()
			except Exception as e:
				print(Colors.RED + 'Error: %s' % e + Colors.ENDC)
				print(traceback.format_exc())


if __name__ == '__main__':
	main()
