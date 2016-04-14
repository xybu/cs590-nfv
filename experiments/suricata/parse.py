#!/usr/bin/python3

import csv
import json
import os
import sys

from dataparser import eve
from dataparser import mon
from dataparser import exceptions


DATA_VALUT_DIR = "/scratch/bu1/suricataV5"

evecollections = dict()
netstatcollections = dict()
sysstatcollections = dict()
psstatcollections = dict()
eveparser = eve.EveParser()
sysstatparser = mon.SysStatParser()
netstatparser = mon.NetStatParser()
psstatparser = mon.PsStatParser()


def get_all_logdirs(path):
	all_logdirs = sorted([i for i in os.listdir(path) if i.startswith('logs')])
	return all_logdirs


def get_collection(collections, name, default_class):
	if name not in collections:
		c = collections[name] = default_class(name)
	else:
		c = collections[name]
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


def traverse_logdir(path):
	all_logdirs = get_all_logdirs(path)
	for dirname in all_logdirs:
		prefix, engine, ts, trace, nworker, args = dirname.split(',', maxsplit=5)
		parse_eve(path + '/' + dirname + '/eve.json', engine, ts, trace, nworker, args)
		parse_netstat(path + '/' + dirname + '/netstat.tcpreplay.em2.csv', engine, ts, trace, nworker, args + ',nicout')
		parse_netstat(path + '/' + dirname + '/netstat.enp34s0.csv', engine, ts, trace, nworker, args + ',nicin')
		parse_sysstat(path + '/' + dirname + '/sysstat.receiver.csv', engine, ts, trace, nworker, args + ',receiver')
		parse_psstat(path + '/' + dirname + '/psstat.suricata.csv', engine, ts, trace, nworker, args)
		parse_psstat(path + '/' + dirname + '/psstat.docker.csv', engine, ts, trace, nworker, args)
		parse_psstat(path + '/' + dirname + '/psstat.qemu.csv', engine, ts, trace, nworker, args)


def main():
	try:
		os.mkdir('data')
		os.chdir('data')
		print(os.getcwd())
	except:
		pass
	traverse_logdir(DATA_VALUT_DIR)
	for col in (evecollections, netstatcollections, sysstatcollections, psstatcollections):
		for name, collection in col.items():
			collection.to_xlsx()


if __name__ == '__main__':
	main()
