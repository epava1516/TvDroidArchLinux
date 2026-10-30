#!/usr/bin/env python3
"""Bounded guest clock/jitter baseline; no clock changes or graphics workload."""
import argparse
import json
from pathlib import Path
import statistics
import time

parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
parser.add_argument('--seconds', type=int, default=20, choices=range(1, 61))
args = parser.parse_args()
source_path = Path('/sys/devices/system/clocksource/clocksource0/current_clocksource')
clocks = {'monotonic': time.CLOCK_MONOTONIC, 'raw': time.CLOCK_MONOTONIC_RAW,
          'boottime': time.CLOCK_BOOTTIME, 'realtime': time.CLOCK_REALTIME}
start = {name: time.clock_gettime_ns(clock) for name, clock in clocks.items()}
source_before = source_path.read_text().strip()
samples = []
for _ in range(args.seconds * 10):
    previous = time.monotonic_ns()
    time.sleep(0.1)
    samples.append((time.monotonic_ns() - previous) / 1e6 - 100)
end = {name: time.clock_gettime_ns(clock) for name, clock in clocks.items()}
ordered = sorted(samples)
result = {'scope': 'Short guest baseline only; clocks are not independent host references. No Android or load test.',
          'clocksource_before': source_before, 'clocksource_after': source_path.read_text().strip(),
          'elapsed_seconds': {name: (end[name] - start[name]) / 1e9 for name in clocks},
          'sleep_lateness_ms': {'min': min(samples), 'median': statistics.median(samples),
                                'p95': ordered[(len(ordered) * 95 + 99) // 100 - 1], 'max': max(samples)},
          'samples_ms': samples}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'samples_ms'}))
