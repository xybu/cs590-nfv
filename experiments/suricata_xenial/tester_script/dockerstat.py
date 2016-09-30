#!/usr/bin/python3

import argparse
from datetime import datetime, timedelta
import ciso8601
import json
import sys
# import time
import docker


def poll_stats(container_name, delay_sec, out):
	with docker.Client(base_url='unix://var/run/docker.sock') as cli:
		delta = timedelta(seconds=4)
		try:
			last_timestamp = datetime.today() + timedelta(seconds=-4)
			for stat in cli.stats(container_name, decode=True):
				timestamp = ciso8601.parse_datetime(stat['read'])
				if timestamp - last_timestamp > delta:
					out.write(json.dumps(stat) + '\n')
					last_timestamp = timestamp
				# cpu_percent = (data['cpu_stats']['cpu_usage']['total_usage'] - data['precpu_stats']['cpu_usage']['total_usage']) / (data['cpu_stats']['system_cpu_usage'] - data['precpu_stats']['system_cpu_usage']) * len(data['cpu_stats']['cpu_usage']['percpu_usage'])
		except KeyboardInterrupt:
			return


def main():
	parser = argparse.ArgumentParser(description='Poll stat of a Docker container and write to a file. Note that due to the mechanism of Docker API, this script works as a *filter*.')
	parser.add_argument('name', type=str, help='Name or ID of the docker container.')
	parser.add_argument('--delay', '-d', nargs='?', type=int, default=4, help='Interval, in sec, between two PRINTED polls. Default: 4.')
	parser.add_argument('--out', '-o', nargs='?', type=str, help='Save output to the specified file. If not given, print to stdout.')
	args = parser.parse_args()
	# print(args)
	if args.out is None:
		poll_stats(args.name, args.delay, sys.stdout)
	else:
		with open(args.out, 'w') as f:
			poll_stats(args.name, args.delay, f)


if __name__ == '__main__':
	main()
