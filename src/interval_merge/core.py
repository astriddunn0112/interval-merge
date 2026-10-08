"""Core operations on sets of half-open intervals.

Representation
--------------
A set of points is represented as a sorted list of disjoint
``(start, end)`` pairs where ``start < end``. Half-open means the
start is included and the end is excluded, so ``[1, 3)`` covers the
points 1 and 2 but not 3.

This representation is closed under the operations we need and makes
containment checks trivial: ``lo <= x < hi``. It also makes adjacency
straightforward to collapse: ``[1, 3)`` and ``[3, 5)`` share the point
3 in a way that is invisible to half-open semantics, so they merge into
``[1, 5)``.

Inputs to the public functions are lenient: any iterable of pairs is
accepted, pairs may be given in any order, they may overlap, and they
may be empty or degenerate (``start >= end``). Degenerate pairs carry
no points and are dropped during normalization.

All public functions return freshly allocated lists; inputs are never
mutated.
"""

from typing import Iterable, List, Tuple

# A single half-open interval on the number line. Any orderable type
# works in principle, but the operations are written and tested against
# ints and floats. We bind to ``Tuple`` rather than a NamedTuple so the
# results stay plain tuples that are easy to compare in tests.
Interval = Tuple[float, float]


def normalize(intervals: Iterable[Tuple[float, float]]) -> List[Interval]:
    """Sort a set of intervals and collapse overlaps and adjacencies.

    Degenerate intervals where ``start >= end`` are dropped: they
    contain no points under half-open semantics, so keeping them would
    only complicate every downstream operation.

    Adjacent intervals (the end of one equals the start of the next)
    are merged. Under half-open semantics ``[1, 3)`` and ``[3, 5)`` do
    not share any point, but together they cover ``[1, 5)`` without
    gaps, so representing them as a single pair is lossless and keeps
    the canonical form minimal.

    Returns a new list; the input iterable is consumed but not stored.
    """
    kept: List[Interval] = [
        (start, end) for start, end in intervals if start < end
    ]
    kept.sort(key=lambda iv: (iv[0], iv[1]))

    result: List[Interval] = []
    for start, end in kept:
        if result and start <= result[-1][1]:
            # Overlaps or touches the previous interval's end. Because
            # the input is sorted by start, the previous interval's
            # start is <= this one's, so we only need to possibly extend
            # the end.
            prev_start, prev_end = result[-1]
            result[-1] = (prev_start, max(prev_end, end))
        else:
            result.append((start, end))
    return result


def merge(intervals: Iterable[Tuple[float, float]]) -> List[Interval]:
    """Alias for :func:`normalize`.

    ``merge`` reads more naturally at call sites that are conceptually
    "combine these ranges", while ``normalize`` reads better inside the
    implementation. Both names exist for readability; they are the same
    function.
    """
    return normalize(intervals)


merge = normalize


def union(
    *sets: Iterable[Tuple[float, float]],
) -> List[Interval]:
    """Union of any number of interval sets.

    Implemented as a single flatten-then-normalize pass. We could call
    ``normalize`` on each argument and then merge the two canonical
    forms, but that does more comparisons than necessary. Flattening
    everything first lets the sort see all starts together, which is
    the same asymptotic cost and simpler code.
    """
    flat: List[Tuple[float, float]] = []
    for s in sets:
        flat.extend(s)
    return normalize(flat)


def subtract(
    a: Iterable[Tuple[float, float]],
    b: Iterable[Tuple[float, float]],
) -> List[Interval]:
    """Set difference: points in ``a`` but not in ``b``.

    Both inputs are normalized first so we can walk them as two sorted
    streams. The algorithm advances a cursor through ``b`` and, for
    each interval in ``a``, emits the pieces of it that fall outside
    every ``b`` interval covering that span.

    The key invariant is that ``bj`` is the first interval in ``b``
    that could still overlap the current piece of ``a``. Because both
    lists are sorted and disjoint, once a ``b`` interval ends at or
    before a piece's start, it can never matter again and we advance.
    """
    a_norm = normalize(a)
    b_norm = normalize(b)

    result: List[Interval] = []
    bi = 0
    n = len(b_norm)

    for a_start, a_end in a_norm:
        # Walk through the b intervals that could intersect [a_start, a_end).
        # We slice the a-interval against each overlapping b-interval and
        # emit the leftover left portion; the right portion is re-examined
        # against the next b-interval.
        piece_start = a_start
        while bi < n and b_norm[bi][0] < a_end:
            b_start, b_end = b_norm[bi]
            if b_end <= piece_start:
                # This b is entirely left of the remaining piece; skip it.
                bi += 1
                continue
            if b_start > piece_start:
                # There is a gap between the piece and this b: emit it.
                result.append((piece_start, b_start))
            # Advance the piece past the part b covers. b_end > piece_start
            # here, so the piece shrinks (possibly to empty).
            piece_start = b_end
            if piece_start >= a_end:
                break
            bi += 1
        if piece_start < a_end:
            result.append((piece_start, a_end))

    # Result is built from sorted, disjoint inputs in order, so it is
    # already normalized.
    return result


def intersect(
    a: Iterable[Tuple[float, float]],
    b: Iterable[Tuple[float, float]],
) -> List[Interval]:
    """Set intersection of two interval sets.

    Walks the two normalized streams together. At each step we look at
    the current interval in each stream and emit their overlap, if any,
    then advance whichever stream's current interval ends first. This
    is the standard two-pointer merge and costs O(len(a) + len(b)).
    """
    a_norm = normalize(a)
    b_norm = normalize(b)

    result: List[Interval] = []
    i = 0
    j = 0
    m = len(a_norm)
    n = len(b_norm)

    while i < m and j < n:
        a_start, a_end = a_norm[i]
        b_start, b_end = b_norm[j]
        lo = max(a_start, b_start)
        hi = min(a_end, b_end)
        if lo < hi:
            result.append((lo, hi))
        # Advance whichever ends first. If they end at the same point,
        # advancing either is correct; we advance both to avoid a
        # pointless extra iteration comparing an empty overlap.
        if a_end <= b_end:
            i += 1
        if b_end <= a_end:
            j += 1

    return result
