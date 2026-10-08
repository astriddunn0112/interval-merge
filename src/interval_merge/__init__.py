"""interval_merge: merge, subtract and intersect half-open intervals.

A half-open interval [start, end) includes start and excludes end.
The empty interval set is represented as an empty list.
"""

from .core import normalize, merge, subtract, intersect, union

__all__ = ["normalize", "merge", "subtract", "intersect", "union"]
