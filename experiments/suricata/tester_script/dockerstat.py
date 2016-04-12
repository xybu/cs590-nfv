#!/usr/bin/python3

# import json
import sys
import time
import docker

container_name = sys.argv[1]
log_filename = sys.argv[2]
interval_sec = int(sys.argv[3])

cli = docker.Client(base_url='unix://var/run/docker.sock')
with open(log_filename, 'wb') as f:
	try:
		for stat in cli.stats(container_name):
			# stat = stat.decode('utf-8')
			f.write(stat)
			# data = json.loads(stat)
			# cpu_percent = (data['cpu_stats']['cpu_usage']['total_usage'] - data['precpu_stats']['cpu_usage']['total_usage']) / (data['cpu_stats']['system_cpu_usage'] - data['precpu_stats']['system_cpu_usage']) * len(data['cpu_stats']['cpu_usage']['percpu_usage'])
			# print(cpu_percent * 100)
			time.sleep(interval_sec)
	except KeyboardInterrupt:
		pass
