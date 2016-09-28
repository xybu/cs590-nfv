import time

import bc_base
from bc_utils import log


class BenchmarkSuricata(bc_base.BenchmarkBase):

    def __init__(self):
        pass

    def wait_for_suricata(self, remote_tmpdir, prepend_cmd=None, poll_interval_sec=8):
        if prepend_cmd is None:
            prepend_cmd = []
        while True:
            if self.remote_call(prepend_cmd + ['test', '-f', remote_tmpdir + '/eve.json']) != 0:
                log('Waiting for %d sec for Suricata to stabilize...' % poll_interval_sec)
                time.sleep(poll_interval_sec)
            else:
                log('Suricata is ready.')
                return

