# coding: utf-8
"""
    KnuthMorrisPratt algorithm.
    Used modules in kmp.py :
    --from future import generators
    --itertools
"""

from __future__ import generators
from itertools import izip, cycle, tee


# Knuth-Morris-Pratt string matching.
def KnuthMorrisPratt(text, pattern):
    """
    Yields all starting positions of copies of the pattern in the text.
    Calling conventions are similar to string.find, but its arguments can be
    lists or iterators, not just strings, it returns all matches, not just
    the first one, and it does not need the whole text in memory at once.
    Whenever it yields, it will have read the text exactly up to and including
    the match that caused the yield.
    --------------------------------------------------------------------------
    @param text -- From what we search pattern.
    @param pattern -- Patter we want to find in text.
    --------------------------------------------------------------------------
    """

    # Allow indexing into pattern and protect against change during yield.
    pattern = list(pattern)

    # build table of shift amounts
    shifts = [1] * (len(pattern) + 1)
    shift = 1
    for pos in range(len(pattern)):
        while shift <= pos and pattern[pos] != pattern[pos-shift]:
            shift += shifts[pos-shift]
        shifts[pos+1] = shift

    # Do the actual search.
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
