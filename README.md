# interval_merge

Merge, subtract and intersect sets of half-open intervals. Half-open means `[start, end)` includes `start` and excludes `end`.

```python
from interval_merge import normalize, union, subtract, intersect

# normalize: sort, drop empties, collapse overlaps and adjacencies
normalize([(5, 7), (1, 3), (3, 4)])   # -> [(1, 7)]

# union: any number of sets
union([(0, 2)], [(1, 6)], [(5, 7)])    # -> [(0, 7)]

# subtract: points in a but not in b
subtract([(0, 10)], [(3, 4), (6, 8)])  # -> [(0, 3), (4, 6), (8, 10)]

# intersect: points in both
intersect([(0, 3), (5, 8)], [(2, 6)])  # -> [(2, 3), (5, 6)]
```

A set of points is represented as a sorted list of disjoint `(start, end)` pairs with `start < end`. Inputs are lenient: any iterable of pairs, in any order, with overlaps or degenerate entries, is accepted. Every public function returns a fresh list and never mutates its input.

## Why this exists

The recurring task of "take some ranges, fold overlaps, punch holes" shows up in scheduling, buffer management, and interval trees. Doing it ad hoc each time is where off-by-one errors live. This library is one small, dependency-free module with the four operations that cover the common cases. The trade-off: it operates on in-memory lists only, and it is not optimized for streaming over huge inputs (sort-then-scan, O(n log n)).

## The awkward edge

Half-open intervals make `[1, 3)` and `[3, 5)` adjacent rather than overlapping: they share the point 3, which the first excludes and the second includes. `normalize` and `union` collapse such adjacencies into `[1, 5)` because together they cover that span without gaps. `intersect`, however, returns `[]` for `[1, 3)` against `[3, 5)` — they share no point. If you expect adjacency to count as overlap in intersection, half-open semantics disagrees, and this library follows half-open semantics strictly.

Degenerate input pairs where `start >= end` are silently dropped: they contain no points, and keeping them would only complicate every downstream operation.

## Exported names

- `normalize(intervals)` — canonical sorted, disjoint form.
- `merge(intervals)` — alias for `normalize`; same function object.
- `union(*sets)` — union of any number of interval sets.
- `subtract(a, b)` — set difference.
- `intersect(a, b)` — set intersection.

## Running the tests

```
PYTHONPATH=src python -m unittest discover -s tests
```

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

## Limitations

Values are coerced to floats, so very large integers lose precision. If you need
exact integer aggregates over a window, this is the wrong tool.

