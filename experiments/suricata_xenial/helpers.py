from datetime import datetime
import socket
import subprocess
import time

import spur
from colors import Colors


HOSTNAME = socket.gethostname()
# Load environment variables from bash INI.
with open('./config/config.%s.ini' % HOSTNAME, 'r') as f:
	exec(f.read())


def log(s):
	print(Colors.MAGENTA + '[' + str(datetime.today()) + '] ' + Colors.ENDC + s)
