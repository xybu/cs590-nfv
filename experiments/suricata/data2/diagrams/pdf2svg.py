import os
import subprocess

for filename in os.listdir('.\cropped'):
	if filename.endswith('.pdf'):
		subprocess.call(['S:\pdf2svg-windows-master\dist-64bits\pdf2svg.exe',
			'.\cropped\\' + filename, filename + '.svg', '1'])
