#!/usr/bin/env python3
"""Inspect the bounded known-media HAL dump; never infer APK compatibility.

The WAV preserves the captured accepted samples. Metrics distinguish signal,
silence and nominal sample duration from clock or acoustic-output evidence.
"""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import sys
import wave


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_capture(data, audioflinger_envelope=False):
    limit = 2 * 1024 * 1024 + (512 * 1024 if audioflinger_envelope else 16384)
    if len(data) > limit:
        raise ValueError('Capture exceeds the selected observation bound')
    prefix = b''
    if audioflinger_envelope:
        marker = b'ARCHTV_ACCEPTED_PCM_V1\n'
        if data.count(marker) != 1:
            raise ValueError('Require one complete HAL observation in the original AF dump')
        index = data.index(marker)
        prefix, data = data[:index], data[index:]
        if b'## BEGIN HAL dump' not in prefix:
            raise ValueError('Missing original AudioFlinger HAL forwarding section')
    magic, header, body = data.split(b'\n', 2)
    if magic != b'ARCHTV_ACCEPTED_PCM_V1' or len(header) > 512:
        raise ValueError('Not the exact original Binder dump framing')
    keys = ['rate', 'channels', 'frame_bytes', 'format', 'total_frames',
            'captured_bytes', 'writes', 'flags', 'hw_params_bytes', 'status_bytes',
            'hw_error', 'status_error', 'producer_pid', 'producer_tid']
    fields = header.split()
    if len(fields) != len(keys) or any(not x.isdigit() for x in fields):
        raise ValueError('Malformed numeric observation header')
    meta = dict(zip(keys, map(int, fields)))
    if [meta[k] for k in ['rate', 'channels', 'frame_bytes', 'format']] != [48000, 2, 4, 0]:
        raise ValueError('Only the selected PCM16 stereo48k observation is supported')
    h, s, n = (meta[k] for k in ['hw_params_bytes', 'status_bytes', 'captured_bytes'])
    expected = h + s + n
    if (h > 4096 or s > 4096 or n > 2 * 1024 * 1024 or n % 4 or
            len(body) < expected or (not audioflinger_envelope and len(body) != expected)):
        raise ValueError('Truncated, oversized or trailing dump bytes')
    if audioflinger_envelope:
        suffix = body[expected:]
        if len(prefix) + len(suffix) > 512*1024:
            raise ValueError('Original AF envelope exceeds the bound')
        meta['transport_envelope'] = {'kind': 'original AudioFlinger --hal dump',
            'prefix_bytes': len(prefix), 'prefix_sha256': digest(prefix),
            'suffix_bytes': len(suffix), 'suffix_sha256': digest(suffix),
            'scope': 'Original surrounding dump retained in the input artifact; not source samples.'}
    meta['producer_read_hw_params'] = body[:h].decode(errors='replace')
    meta['producer_read_pcm_status'] = body[h:h+s].decode(errors='replace')
    return meta, body[h+s:expected]


def signal_metrics(pcm):
    samples = array.array('h')
    samples.frombytes(pcm)
    if sys.byteorder != 'little':
        samples.byteswap()
    left, right = samples[::2], samples[1::2]
    rows = []
    coefficient = 2 * math.cos(2 * math.pi * 1000 / 48000)
    for start in range(0, len(left), 960):
        block = left[start:start+960]
        energy = sum(x*x for x in block)
        a = b = 0.0
        for x in block:
            value = x + coefficient*a - b
            b, a = a, value
        power = a*a + b*b - coefficient*a*b
        rows.append({'start_frame': start, 'frames': len(block),
                     'rms_pcm16': math.sqrt(energy/len(block)),
                     'nominal_1khz_power_ratio': 2*power/(len(block)*energy) if energy else None})
    peak_rms = max((x['rms_pcm16'] for x in rows), default=0)
    threshold = max(2.0, peak_rms/20)
    active = [x for x in rows if x['rms_pcm16'] > threshold]
    return {'frames': len(left), 'nominal_sample_duration_seconds': len(left)/48000,
            'peak_abs_pcm16': max((abs(x) for x in samples), default=0),
            'peak_window_rms_pcm16': peak_rms,
            'active_threshold_pcm16': threshold,
            'active_nominal_seconds': sum(x['frames'] for x in active)/48000,
            'nominal_1khz_active_seconds': sum(x['frames'] for x in active
                if x['nominal_1khz_power_ratio'] is not None and
                   x['nominal_1khz_power_ratio'] >= .8)/48000,
            'identical_stereo_frames': sum(a == b for a, b in zip(left, right)),
            'windows': rows}


def chirp_trace(pcm):
    """Measure zero crossings for the exact generated400+400*t source only.

    Derived nominal source times are diagnostic estimates under resampling,
    not wall-clock, sample-exact alignment, acoustic output or acceptance.
    """
    samples = array.array('h')
    samples.frombytes(pcm)
    if sys.byteorder != 'little':
        samples.byteswap()
    left = samples[::2]
    peak_rms = max((math.sqrt(sum(x*x for x in left[i:i+960]) /
                    len(left[i:i+960])) for i in range(0, len(left), 960)), default=0)
    threshold = max(2.0, peak_rms/20)
    rows = []
    for start in range(0, len(left), 960):
        block = left[start:start+960]
        rms = math.sqrt(sum(x*x for x in block)/len(block))
        crossings = [i - block[i]/(block[i+1]-block[i])
                     for i in range(len(block)-1) if block[i] <= 0 < block[i+1]]
        frequency = None
        variation = None
        if rms > threshold and len(crossings) >= 4:
            periods = [b-a for a,b in zip(crossings, crossings[1:])]
            period = sum(periods)/len(periods)
            variation = math.sqrt(sum((x-period)**2 for x in periods)/len(periods))/period
            frequency = 48000/period
        rows.append({'accepted_start_frame': start, 'frames': len(block),
                     'rms_pcm16': rms, 'estimated_frequency_hz': frequency,
                     'period_relative_deviation': variation,
                     'estimated_source_seconds': (frequency-400)/400
                         if frequency is not None and 350 <= frequency <= 2050 else None})
    identified = [x['estimated_source_seconds'] for x in rows
                  if x['estimated_source_seconds'] is not None and
                  x['period_relative_deviation'] < .1]
    return {'source_equation': 'frequency=400+400*t Hz,0<=t<4s',
            'active_threshold_pcm16': threshold, 'windows': rows,
            'estimated_source_time_min': min(identified, default=None),
            'estimated_source_time_max': max(identified, default=None),
            'scope': 'Zero-crossing estimates for known chirp. Resampling, gain/noise, gaps, replay and flush affect mapping; no automatic coverage/sync/audio verdict.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--reference', required=True, type=Path,
                        help='Host-decoded known reference PCM16 stereo48k, not another capture')
    parser.add_argument('--reference-sha256', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--audioflinger-envelope', action='store_true',
                        help='Explicitly retain/validate original AF text around the HAL binary section')
    parser.add_argument('--timecoded-chirp', action='store_true',
                        help='Estimate source times for the pinned400+400*t Hz/4s chirp only')
    args = parser.parse_args()
    if args.capture.stat().st_size > 2*1024*1024 + (512*1024 if args.audioflinger_envelope else 16384):
        raise ValueError('Refuse unbounded capture read')
    data = args.capture.read_bytes()
    meta, pcm = parse_capture(data, args.audioflinger_envelope)
    if args.reference.stat().st_size > 2*1024*1024:
        raise ValueError('Refuse unbounded known-reference read')
    reference = args.reference.read_bytes()
    if digest(reference) != args.reference_sha256 or len(reference) % 4:
        raise ValueError('Reference identity or frame shape mismatch')
    result = {'capture_path': str(args.capture.resolve()), 'capture_sha256': digest(data),
              'producer_metadata': meta, 'raw_sample_sha256': digest(pcm),
              'captured_byte_count_consistent': meta['flags'] == 0 and meta['writes'] > 0 and
                  meta['total_frames'] * 4 == len(pcm),
              'captured_signal': signal_metrics(pcm),
              'reference_path': str(args.reference.resolve()),
              'reference_sha256': digest(reference), 'reference_signal': signal_metrics(reference),
              'scope': 'Known-media signal metrics only. Producer proc read is separate from external identity/MAC proof. Accepted samples are not acoustic output, clock accuracy, source completeness, A/V sync or APK compatibility. Constant1kHz reference cannot uniquely identify source time/coverage; active thresholds and power ratios are diagnostic, not acceptance gates.'}
    if args.timecoded_chirp:
        if digest(reference) != '122b47920fea0b78e73301660761039b55673a965efdcfdb3e86d5df2a0db75f':
            raise ValueError('Timecoded mode requires the exact pinned chirp reference')
        result['timecoded_capture'] = chirp_trace(pcm)
        result['timecoded_reference'] = chirp_trace(reference)
    args.out.mkdir(parents=True, exist_ok=False)
    wav_path = args.out/'accepted-signal.wav'
    with wave.open(str(wav_path), 'wb') as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(pcm)
    result['wav_path'] = str(wav_path.resolve())
    result['wav_sha256'] = digest(wav_path.read_bytes())
    (args.out/'signal-analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['captured_byte_count_consistent', 'raw_sample_sha256',
                                            'wav_path']}))
    print(json.dumps({k: v for k, v in result['captured_signal'].items() if k != 'windows'}))


if __name__ == '__main__':
    main()
