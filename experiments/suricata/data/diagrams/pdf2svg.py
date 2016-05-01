import os
import subprocess

for filename in os.listdir('.'):
	if filename.endswith('.pdf'):
		subprocess.call(['S:\pdf2svg-windows-master\dist-64bits\pdf2svg.exe',
			filename, filename + '.svg', '1'])
