"""
Parser of sysmon.py.

@author	Xiangyu Bu <bu1@purdue.edu>
"""

import csv

import xlsxwriter

import excelhelper
import exceptions


def get_collection_name(engine, ts, trace, nworker, args):
	return ','.join([engine, trace, nworker, args])


class NetStatCollection:
	HEADER = ['Timestamp', 'Uptime', 'NIC', 'bytes_sent', 'bytes_recv', 'packets_sent', 'packets_recv', 'errin', 'errout', 'dropin', 'dropout']

	def __init__(self, name):
		self.name = name
		self.all_data = dict()
		print('Created new netstat collection: "%s"' % name)

	def get_key(self, engine, ts, trace, nworker, args):
		return ts

	def add(self, key, data):
		self.all_data[key] = data

	def to_xlsx(self):
		with open('%s,netstat.log' % self.name, 'w') as f:
			workbook = xlsxwriter.Workbook('%s,netstat.xlsx' % self.name, {'strings_to_numbers': True})
			summary_sheet = workbook.add_worksheet('Summary')
			sheet_names = []
			max_rowcount = 0
			for key in sorted(self.all_data.keys()):
				sheet_name = str(key)
				data = self.all_data[key]
				sheet = workbook.add_worksheet(sheet_name)
				sheet_names.append(sheet_name)
				for i, column_name in enumerate(self.HEADER):
					sheet.write(0, i, column_name)
					sheet.set_column('{0}:{0}'.format(chr(ord('A') + i)), 12)
				print('Sheet name: %s' % sheet_name, file=f)
				print('  Records: %d' % len(data), file=f)
				if max_rowcount < len(data):
					max_rowcount = len(data)
				for rowid, row in enumerate(data):
					for colid, col in enumerate(row):
						sheet.write(rowid+1, colid, col)
			for i, column_name in enumerate(self.HEADER):
				summary_sheet.write(0, i, column_name)
				summary_sheet.set_column('{0}:{0}'.format(chr(ord('A') + i)), 12)
			for i in range(1, max_rowcount+1):
				for j in range(len(self.HEADER)):
					related_cells = []
					for s in sheet_names:
						related_cells.append('%s!%s' % (s, excelhelper.excel_style(i+1, j+1)))
					# print(related_cells)
					summary_sheet.write(i, j, '=INT(MEDIAN(%s))' % ','.join(related_cells))
			workbook.close()
		print('Saved "%s,eve.xlsx"' % self.name)	

class NetStatParser:
	"""
	Parse netstat.csv output by sysmon.
	"""

	def __init__(self):
		pass

	def parse(self, path):
		data = []
		with open(path, 'rU') as f:
			reader = csv.reader(f)
			try:
				header = next(reader)
			except StopIteration:
				raise exceptions.NoContentException('Netstat file "%s" is empty.' % path)
			# data.append(header)
			for row in reader:
				data.append(row)
		return data
