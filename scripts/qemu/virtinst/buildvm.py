#!/usr/bin/python3

"""
A parser that converts an INI file to arguments of virt-install.

Usage: buildvm.py config-file-path

By default, it converts all key=value pairs to two arguments --key value.

For example, the section

[identity]
name = ubuntu

will be translated to "--name ubuntu". The section name has no effect.

Two special section specifiers:
.expand (collapse all key=value pairs to a single argument;the same name key is put as first), and
.options (only add --key. value has no effect)

For example, the section

[graphics.expand]
graphics = vnc
password = foobar

will be converted to "--graphics vnc,password=foobar". The section name is the key.

and the section

[misc.options]
check-cpu =

will be converted to "--check-cpu". The section name has no effect.


@author Xiangyu Bu <bu1@purdue.edu>
"""

import configparser
import os
import subprocess
import sys


def to_args(config):
  args = ['sudo', 'virt-install']
  for section in config.sections():
    if section.endswith('.options'):
      for k in config[section]:
        args.append('--' + str(k))
    elif section.endswith('.expand'):
      argn = section[:-7]
      argv = ''
      for k in config[section]:
        v = str(config[section][k])
        if k == argn:
          argv = v + ',' + argv
        else:
          argv = argv + ('%s=%s,' % (k, v))
      if argv.startswith(','):
        argv = argv[1:]
      if argv.endswith(','):
        argv = argv[:-1]
      args.append('--' + argn)
      args.append(argv)
    else:
      for k in config[section]:
        args.append('--' + k)
        args.append(config[section][k])
  return args


def print_usage():
  print('Usage: %s PATH' % sys.argv[0])
  print('  PATH: path to the config file.')
  sys.exit(1)


def main():
  if len(sys.argv) != 2:
    print('\033[91mError: invalid arguments.\033[0m')
    print_usage()
  
  config = configparser.ConfigParser()
  with open(sys.argv[1], 'r') as f:
    config.read_file(f)
    
  args = to_args(config)
  print(args)

  subprocess.call(args)


if __name__ == '__main__':
  main()
