#!/usr/bin/python3

import threading

import xlsxwriter

from . import excelhelper
from . import exceptions

def flatten_dict(d):
	# http://codereview.stackexchange.com/questions/21033/flatten-dictionary-in-python-functional-style
  def items():
      for key, value in d.items():
          if isinstance(value, dict):
              for subkey, subvalue in flatten_dict(value).items():
                  yield key + "." + subkey, subvalue
          else:
              yield key, value
  return dict(items())


class SnortOutCollection:

	def __init__(self, name):
		self._lock = threading.Lock()
		self.name = name
		self.all_data = dict()
		print('Created new snort.out collection: "%s"' % name)

	def get_key(self, engine, ts, trace, nworker, args):
		return ts

	def add(self, key, data):
		self._lock.acquire()
		self.all_data[key] = data
		self._lock.release()

	def to_xlsx0(self):
		print(self.all_data)

	def to_xlsx(self):
		max_colcount = -1
		with open('%s,snortout.log' % self.name, 'w') as f:
			print('Sample size: %d' % len(self.all_data), file=f)
			workbook = xlsxwriter.Workbook('%s,snortout.xlsx' % self.name, {'strings_to_numbers': True})
			summary_sheet = workbook.add_worksheet('Summary')
			sheet_names = []
			for out_id in sorted(self.all_data.keys()):
				sheet_name = str(out_id)
				sheet_names.append(sheet_name)
				sheet = workbook.add_worksheet(sheet_name)
				data = flatten_dict(self.all_data[out_id])
				for i, k in enumerate(sorted(data.keys())):
					sheet.write(0, i, k)
					sheet.write(1, i, data[k])
				if max_colcount < len(data):
					max_colcount = len(data)
				print('Sheet name: %s' % out_id, file=f)
			for j in range(max_colcount):
				related_cells = []
				for s in sheet_names:
					related_cells.append('%s!%s' % (s, excelhelper.excel_style(2, j+1)))
				# print(related_cells)
				summary_sheet.write(0, j, '=\'%s\'!%s' % (sheet_names[0], excelhelper.excel_style(1, j+1)))
				summary_sheet.write(1, j, '=INT(MEDIAN(%s))' % ','.join(related_cells))
			workbook.close()
		print('Saved "%s,snortout.xlsx"' % self.name)
