#!/usr/bin/python3

import csv
import json
import os
import sys

import eve
import mon
import exceptions


DATA_VALUT_DIR = "/scratch/bu1/suricataV4"

evecollections = dict()
netstatcollections = dict()
eveparser = eve.EveParser()
netstatparser = mon.NetStatParser()


def get_all_logdirs(path):
	all_logdirs = sorted([i for i in os.listdir(path) if i.startswith('logs')])
	return all_logdirs


def parse_eve(eve_path, engine, ts, trace, nworker, args):
	if os.path.isfile(eve_path):
		print('Processing "%s"...' % eve_path)
		eve_collection_name = eve.get_collection_name(engine, ts, trace, nworker, args)
		if eve_collection_name not in evecollections:
			evecollection = evecollections[eve_collection_name] = eve.EveCollection(eve_collection_name)
		else:
			evecollection = evecollections[eve_collection_name]
		try:
			eve_id = evecollection.get_key(engine, ts, trace, nworker, args)
			eve_data = eveparser.parse(eve_path)
			evecollection.add_eve(eve_id, eve_data)
		except exceptions.NoContentException as ex:
			print('Error: ' + str(ex))


def parse_netstat(path, engine, ts, trace, nworker, args):
	if os.path.isfile(path):
		print('Processing "%s"...' % path)
		name = mon.get_collection_name(engine, ts, trace, nworker, args)
		if name not in netstatcollections:
			collection = netstatcollections[name] = mon.NetStatCollection(name)
		else:
			collection = netstatcollections[name]
		try:
			netstat_id = collection.get_key(engine, ts, trace, nworker, args)
			data = netstatparser.parse(path)
			collection.add(netstat_id, data)
		except exceptions.NoContentException as ex:
			print('Error: ' + str(ex))


def traverse_logdir(path):
	all_logdirs = get_all_logdirs(path)
	for dirname in all_logdirs:
		prefix, engine, ts, trace, nworker, args = dirname.split(',', maxsplit=5)
		if engine == 'bm' and nworker == '1':
			parse_eve(path + '/' + dirname + '/eve.json', engine, ts, trace, nworker, args)
			parse_netstat(path + '/' + dirname + '/netstat.em2.tcpreplay.csv', engine, ts, trace, nworker, args+',tcpreplay')


def main():
	traverse_logdir(DATA_VALUT_DIR)
	for name, collection in evecollections.items():
		collection.to_xlsx()
	for name, collection in netstatcollections.items():
		collection.to_xlsx()


if __name__ == '__main__':
	main()
