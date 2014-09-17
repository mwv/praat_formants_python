#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: praat_formants_python.py
# date: Mon September 08 19:58 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""praat_formants_python: extract formants from praat into python

"""

from __future__ import division

from subprocess import Popen, PIPE
import warnings
from bisect import bisect_left, bisect_right
import tempfile

import numpy as np

_script_loc = None
def make_script():
    global _script_loc
    if _script_loc is None:
        _script_loc = tempfile.mktemp(suffix='.praat')
        with open(_script_loc, 'w') as fid:
            fid.write("""# take name of wav file from stdin and dump formant table to stdout
form File
sentence filename
positive maxformant 5500
real winlen 0.025
positive preemph 50
endform
Read from file... 'filename$'
To Formant (burg)... 0.01 5 'maxformant' 'winlen' 'preemph'
List... no yes 6 no 3 no 3 no
exit""")
    return _script_loc


class PraatError(Exception):
    pass


def run_praat(*args):
    """Run praat with `args` and return results as a c string

    Arguments:
    :param *args: command line arguments to pass to praat.
    """
    p = Popen(['praat'] + map(str, list(args)),
              shell=False,
              stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    if p.returncode:
        raise PraatError(''.join(stderr.readlines()))
    else:
        return stdout


_fmt_cache = {}
def file2formants(filename, maxformant=5500, winlen=0.025, preemph=50,
                  memoize_call=True):
    """Extract formant table from audio file using praat.
    The return array is laid out as:
    [[time, f1, f2, f3],
     ..]

    Formants that praat returns as undefined are represented as NaNs. This
    function can be memoized to minimize the number of calls to praat.

    Arguments:
    :param filename: filename of audio file
    :param maxformant: formant ceiling (use 5500 for female speech, 5000 for male)
    :param winlen: window length in seconds [0.025]
    :param preemph: pre-emphasis [50]
    :param memoize_call: Memoize the calls to praat. Use `clear_formant_cache()`
      to reset the cache.
    """
    def _float(s):
        try:
            return float(s)
        except ValueError:
            return np.nan

    if memoize_call:
        key = (filename, maxformant, winlen, preemph)
        if not key in _fmt_cache:
            res = run_praat(make_script(),
                            filename, maxformant, winlen, preemph)
            _fmt_cache[key] = np.array(map(lambda x: map(_float, x.rstrip().split('\t')[:4]),
                               res.split('\n')[1:-1]))
        return _fmt_cache[key]
    else:
        res = run_praat(make_script(),
                        filename, maxformant, winlen, preemph)
        return np.array(map(lambda x: map(_float, x.rstrip().split('\t')[:4]),
                        res.split('\n')[1:-1]))


def clear_formant_cache():
    """Clear the formant cache.
    """
    global _fmt_cache
    _fmt_cache = {}


def formants_at_time(filename, time, **kwargs):
    """Extract formants in audio file at a time point. Return a 1d array.

    Arguments:
    :param filename: audio file
    :param time: timepoint in seconds at which to extract formants

    For kwargs see the documentation for `file2formants`.
    """
    formants_array = file2formants(filename, **kwargs)
    try:
        res = formants_array[bisect_left(formants_array[:, 0], time), 1:]
    except IndexError:
        raise ValueError, 'time out of range for filelength'
    if np.any(np.isnan(res)):
        warnings.warn('undefined formant found')
    return res


def formants_at_interval(filename, start, end, **kwargs):
    """Extract formants in audio file between start and end times. Returns a
    2-d array.

    Arguments:
    :param filename: audio file
    :param start: start time in seconds
    :param end: end time in seconds

    For kwargs see the documentation for `file2formants`.
    """
    formants_array = file2formants(filename, **kwargs)
    try:
        start_idx = bisect_left(formants_array[:, 0], start)
        end_idx = bisect_right(formants_array[:, 0], end)
        res = formants_array[start_idx: end_idx]
    except IndexError:
        raise ValueError, 'time out of range for filelength'
    if np.any(np.isnan(res)):
        warnings.warn('undefined formant found')
    return res
