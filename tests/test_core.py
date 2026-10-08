import unittest

from interval_merge import normalize, merge, subtract, intersect, union


class TestNormalize(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(normalize([]), [])

    def test_single(self):
        self.assertEqual(normalize([(1, 5)]), [(1, 5)])

    def test_drops_degenerate(self):
        # start == end and start > end both carry no points.
        self.assertEqual(normalize([(3, 3), (5, 2), (1, 4)]), [(1, 4)])

    def test_unsorted_overlapping(self):
        self.assertEqual(
            normalize([(5, 7), (1, 3), (2, 6)]),
            [(1, 7)],
        )

    def test_adjacent_merge(self):
        # [1,3) and [3,5) share the point 3, which is excluded from the
        # first and included in the second, so they union to [1,5).
        self.assertEqual(normalize([(1, 3), (3, 5)]), [(1, 5)])

    def test_contained(self):
        self.assertEqual(normalize([(0, 10), (2, 4), (6, 8)]), [(0, 10)])

    def test_does_not_mutate_input(self):
        src = [(5, 7), (1, 3)]
        normalize(src)
        self.assertEqual(src, [(5, 7), (1, 3)])


class TestMergeAlias(unittest.TestCase):
    def test_merge_matches_normalize(self):
        self.assertIs(merge, normalize)


class TestUnion(unittest.TestCase):
    def test_two_sets(self):
        self.assertEqual(
            union([(0, 2), (5, 7)], [(1, 6)]),
            [(0, 7)],
        )

    def test_disjoint(self):
        self.assertEqual(
            union([(0, 1)], [(2, 3)], [(5, 6)]),
            [(0, 1), (2, 3), (5, 6)],
        )

    def test_empty_args(self):
        self.assertEqual(union(), [])

    def test_empty_members(self):
        self.assertEqual(union([], [(1, 2)], []), [(1, 2)])


class TestSubtract(unittest.TestCase):
    def test_no_overlap(self):
        self.assertEqual(subtract([(0, 2), (5, 7)], [(3, 4)]), [(0, 2), (5, 7)])

    def test_total_removal(self):
        self.assertEqual(subtract([(0, 5)], [(0, 5)]), [])

    def test_split_middle(self):
        self.assertEqual(subtract([(0, 10)], [(3, 4), (6, 8)]), [(0, 3), (4, 6), (8, 10)])

    def test_clip_left(self):
        self.assertEqual(subtract([(0, 5)], [(0, 2)]), [(2, 5)])

    def test_clip_right(self):
        self.assertEqual(subtract([(0, 5)], [(3, 5)]), [(0, 3)])

    def test_multiple_a_against_one_b(self):
        self.assertEqual(
            subtract([(0, 3), (4, 9)], [(2, 7)]),
            [(0, 2), (7, 9)],
        )

    def test_b_entirely_outside_gap(self):
        # b sits in a hole of a, so nothing is removed.
        self.assertEqual(subtract([(0, 2), (5, 7)], [(3, 4)]), [(0, 2), (5, 7)])

    def test_empty_b(self):
        self.assertEqual(subtract([(0, 2), (3, 5)], []), [(0, 2), (3, 5)])

    def test_empty_a(self):
        self.assertEqual(subtract([], [(0, 2)]), [])

    def test_unsorted_inputs(self):
        # Inputs are normalized internally, so order shouldn't matter.
        self.assertEqual(
            subtract([(5, 9), (0, 3)], [(7, 8), (1, 2)]),
            [(0, 1), (2, 3), (5, 7), (8, 9)],
        )


class TestIntersect(unittest.TestCase):
    def test_no_overlap(self):
        self.assertEqual(intersect([(0, 2)], [(3, 5)]), [])

    def test_partial_overlap(self):
        self.assertEqual(intersect([(0, 4)], [(2, 6)]), [(2, 4)])

    def test_contained(self):
        self.assertEqual(intersect([(0, 10)], [(3, 5)]), [(3, 5)])

    def test_multiple(self):
        self.assertEqual(
            intersect([(0, 3), (5, 8), (10, 12)], [(2, 6), (9, 11)]),
            [(2, 3), (5, 6), (10, 11)],
        )

    def test_shared_boundary(self):
        # [1,3) and [3,5) share only the point 3, which the first
        # excludes and the second includes, so the intersection is empty.
        self.assertEqual(intersect([(1, 3)], [(3, 5)]), [])

    def test_empty_operand(self):
        self.assertEqual(intersect([], [(0, 2)]), [])
        self.assertEqual(intersect([(0, 2)], []), [])

    def test_unsorted_inputs(self):
        self.assertEqual(
            intersect([(5, 8), (0, 3)], [(2, 6), (7, 9)]),
            [(2, 3), (5, 6), (7, 8)],
        )

    def test_equal_endpoints_advance_both(self):
        # When both current intervals end at the same value, we advance
        # both cursors. This test exercises that branch and confirms we
        # don't emit a zero-width interval or skip a real overlap.
        self.assertEqual(
            intersect([(0, 5), (6, 10)], [(2, 8)]),
            [(2, 5), (6, 8)],
        )


if __name__ == "__main__":
    unittest.main()
