from __future__ import generators
from collections import Counter
from itertools import izip, cycle, tee


def most_common(lst):
    return max(set(lst), key=lst.count)


def pairwise(seq):
    a, b = tee(seq)
    next(b)
    return izip(a, b)


# Knuth-Morris-Pratt string matching
# David Eppstein, UC Irvine, 1 Mar 2002
def KnuthMorrisPratt(text, pattern):
    '''Yields all starting positions of copies of the pattern in the text.
Calling conventions are similar to string.find, but its arguments can be
lists or iterators, not just strings, it returns all matches, not just
the first one, and it does not need the whole text in memory at once.
Whenever it yields, it will have read the text exactly up to and including
the match that caused the yield.'''

    # allow indexing into pattern and protect against change during yield
    pattern = list(pattern)

    # build table of shift amounts
    shifts = [1] * (len(pattern) + 1)
    shift = 1
    for pos in range(len(pattern)):
        while shift <= pos and pattern[pos] != pattern[pos-shift]:
            shift += shifts[pos-shift]
        shifts[pos+1] = shift

    # do the actual search
    startPos = 0
    matchLen = 0
    for c in text:
        while matchLen == len(pattern) or \
                matchLen >= 0 and pattern[matchLen] != c:
            startPos += shifts[matchLen]
            matchLen -= shifts[matchLen]
        matchLen += 1
        if matchLen == len(pattern):
            yield startPos


def spi_decoded(voltage_clock, voltage_data, time, sample_interval):
    start_decoding_lin_data = []
    start_decoding_lin_clock = []
    for i in range(len(voltage_data) / sample_interval):
        start_decoding_lin_data.append(
            int(most_common(voltage_data[i * sample_interval:i * sample_interval + sample_interval])))
        start_decoding_lin_clock.append(
            int(most_common(voltage_clock[i * sample_interval:i * sample_interval + sample_interval])))
    br_flagova = 0
    data_final = []
    for s in KnuthMorrisPratt(start_decoding_lin_clock, [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]):
        data_final.append("{0:0>2X}".format(
                int("".join(map(str, start_decoding_lin_data[s:s+16:2])), 2)))
    return data_final
