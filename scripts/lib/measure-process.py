#!/usr/bin/env python3
"""Measure one child process with Linux rusage, without an extra package."""
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

started = time.monotonic()
result = subprocess.run(sys.argv[2:], check=False)
usage = resource.getrusage(resource.RUSAGE_CHILDREN)
Path(sys.argv[1]).write_text(json.dumps({
    'scope': 'one renderer probe, including PNG encoding; not session PSS',
    'elapsed_seconds': time.monotonic() - started,
    'user_cpu_seconds': usage.ru_utime,
    'system_cpu_seconds': usage.ru_stime,
    'max_rss_kib': usage.ru_maxrss,
    'exit_code': result.returncode,
}, indent=2) + '\n')
sys.exit(result.returncode)
