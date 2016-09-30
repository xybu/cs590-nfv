#!/usr/bin/python3

"""
Parse snort statistics output to batch-processing friendly format.
"""

import re


class SnortOutputParser:

	SECTION_SEPARATOR = '=' * 79 + '\n'
	RESULT_SECTION_BEGIN = 1
	NUMBER_RE = re.compile('[\d]+\.*[\d]*')
	INT_RE = re.compile('[\d]+')

	def __init__(self):
		pass

	def _get_value(self, line):
		""" Get the value from a line of format 'kkk: vvv'. """
		return line.split(':')[1].strip()

	def parse_runtime(self, section):
		data = dict()
		for line in section:
			line = line.strip()
			if line.startswith('Run time for packet processing was'):
				data['process_time_sec'] = float(self.NUMBER_RE.search(line).group())
			elif line.startswith('Snort processed'):
				data['total_pkts'] = int(self.INT_RE.search(line).group())
			elif line.startswith('Snort ran for'):
				online_time = self.INT_RE.findall(line)
				data['online_time_sec'] = int(online_time[0]) * 24 * 60 * 60 + int(online_time[1]) * 60 * 60 \
																		+ int(online_time[2]) * 60 + int(online_time[3])
			elif line.startswith('Pkts/min:'):
				data['pkts_per_min'] = int(self._get_value(line))
			elif line.startswith('Pkts/sec:'):
				data['pkts_per_sec'] = int(self._get_value(line))
		self._data['runtime'] = data

	def parse_memory_usage_summary(self, section):
		pass

	def parse_packet_io_totals(self, section):
		data = dict()
		for line in section:
			line = line.strip()
			if line.startswith('Packet I/O Totals'):
				pass
			elif line.startswith('Received:'):
				data['recv_pkts'] = int(self._get_value(line))
			elif line.startswith('Analyzed:'):
				data['analyzed_pkts'] = int(self._get_value(line).split()[0])		# Get rid of percentage.
			elif line.startswith('Dropped:'):
				data['dropped_pkts'] = int(self._get_value(line).split()[0])		# Get rid of percentage.
			elif line.startswith('Filtered:'):
				data['filtered_pkts'] = int(self._get_value(line).split()[0])		# Get rid of percentage.
			elif line.startswith('Outstanding:'):
				data['outstanding_pkts'] = int(self._get_value(line).split()[0])		# Get rid of percentage.
		self._data['pkts_total'] = data

	def parse_packet_breakdown(self, section):
		pass

	def parse_section(self, section):
		""" Section consists of lines between two separators. """
		if section[0].startswith('Run time for packet processing was'):
			self.parse_runtime(section)
		elif section[0].startswith('Memory usage summary:'):
			self.parse_memory_usage_summary(section)
		elif section[0].startswith('Packet I/O Totals:'):
			self.parse_packet_io_totals(section)
		elif section[0].startswith('Breakdown by protocol'):
			self.parse_packet_breakdown(section)
		# Don't bother with other sections.

	def parse(self, path):
		self._data = dict()
		with open(path, 'r') as f:
			content = f.read()
		sections = content.split(self.SECTION_SEPARATOR)
		for s in sections[self.RESULT_SECTION_BEGIN:]:
			self.parse_section(s.split('\n'))
		return self._data
