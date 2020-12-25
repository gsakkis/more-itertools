import copy
import operator as op
import unittest
from functools import partial
from itertools import islice

from more_itertools import StatePolicy, magic_iter, rich_iter

is_odd = lambda x: x % 2 == 1
less_than_3 = lambda x: x < 3


class RichIterTests(unittest.TestCase):
    iter_factory = rich_iter
    state_policy = None

    @classmethod
    def rich_iters(cls, iterable=None):
        if iterable is None:
            iterable = range(1, 6)
        return list(
            cls.iter_factory(i, state_policy=cls.state_policy)
            if cls.state_policy is not None
            else cls.iter_factory(i)
            for i in (
                iterable,
                list(iterable),
                iter(iterable),
                iter(list(iterable)),
            )
        )

    def test_iteration(self):
        for ri in self.rich_iters():
            self.assertEqual(next(ri), 1)
            self.assertEqual(next(ri), 2)
            self.assertEqual(list(ri), [3, 4, 5])
            self.assertRaises(StopIteration, next, ri)
            self.assertEqual(list(ri), [])

    def test_bool(self):
        for ri in self.rich_iters():
            for _ in range(2):
                self.assertTrue(ri)
        for ri in self.rich_iters([]):
            for _ in range(2):
                self.assertFalse(ri)

    def test_peek(self):
        for ri in self.rich_iters():
            for _ in range(2):
                self.assertEqual(ri.peek(), 1)
                self.assertEqual(ri.peek(default=None), 1)
            self.assertEqual(next(ri), 1)

            for _ in range(2):
                self.assertEqual(ri.peek(), 2)
                self.assertEqual(ri.peek(default=None), 2)
            self.assertEqual(next(ri), 2)

            self.assertEqual(list(ri), [3, 4, 5])
            for _ in range(2):
                self.assertIsNone(ri.peek(default=None))
                self.assertRaises(StopIteration, ri.peek)

    def test_copy(self):
        for ri in self.rich_iters():
            ri2 = copy.copy(ri)
            self.assertIs(ri2.__class__, ri.__class__)
            self.assertEqual(list(ri), [1, 2, 3, 4, 5])
            self.assertEqual(list(ri2), [1, 2, 3, 4, 5])

    def test_count(self):
        count = self.iter_factory.count
        if self.state_policy:
            count = partial(count, state_policy=self.state_policy)

        ri = count()
        self.assertEqual(list(islice(ri, 5)), [0, 1, 2, 3, 4])

        ri = count(10)
        self.assertEqual(list(islice(ri, 5)), [10, 11, 12, 13, 14])

        ri = count(step=2)
        self.assertEqual(list(islice(ri, 5)), [0, 2, 4, 6, 8])

        ri = count(10, 2)
        self.assertEqual(list(islice(ri, 5)), [10, 12, 14, 16, 18])

    def test_repeat(self):
        repeat = self.iter_factory.repeat
        if self.state_policy:
            repeat = partial(repeat, state_policy=self.state_policy)

        ri = repeat(10, 3)
        self.assertEqual(list(ri), [10, 10, 10])

        ri = repeat(10)
        self.assertEqual(list(islice(ri, 5)), [10, 10, 10, 10, 10])

    def test_cycle(self):
        for ri in self.rich_iters():
            self.assertEqual(
                list(islice(ri.cycle(), 12)),
                [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2],
            )

    def test_accumulate(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.accumulate()), [1, 3, 6, 10, 15])
        for ri in self.rich_iters():
            self.assertEqual(list(ri.accumulate(op.mul)), [1, 2, 6, 24, 120])

    def test_chain(self):
        for ri in self.rich_iters():
            self.assertEqual(
                list(ri.chain('DEF')), [1, 2, 3, 4, 5, 'D', 'E', 'F']
            )

    def test_chain_from_iterable(self):
        for ri in self.rich_iters(['ABC', ('D', 'E', 'F')]):
            self.assertEqual(list(ri.chain_from_iterable()), list('ABCDEF'))

    def test_compress(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.compress([1, 0, 1, 1, 0])), [1, 3, 4])

    def test_dropwhile(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.dropwhile(less_than_3)), [3, 4, 5])

    def test_filter(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.filter(is_odd)), [1, 3, 5])

    def test_filterfalse(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.filterfalse(is_odd)), [2, 4])

    def test_groupby(self):
        for ri in self.rich_iters('AAAABBBCCDAABBBB'):
            self.assertEqual(
                [(k, ''.join(g)) for k, g in ri.groupby()],
                [
                    ('A', 'AAAA'),
                    ('B', 'BBB'),
                    ('C', 'CC'),
                    ('D', 'D'),
                    ('A', 'AA'),
                    ('B', 'BBBB'),
                ],
            )
        for ri in self.rich_iters('AAAABBBCCDAABBBB'):
            self.assertEqual(
                [(k, ''.join(g)) for k, g in ri.groupby(lambda x: x > 'B')],
                [(False, 'AAAABBB'), (True, 'CCD'), (False, 'AABBBB')],
            )

    def test_islice(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.islice(None)), [1, 2, 3, 4, 5])
        for ri in self.rich_iters():
            self.assertEqual(list(ri.islice(2)), [1, 2])
        for ri in self.rich_iters():
            self.assertEqual(list(ri.islice(2, None)), [3, 4, 5])
        for ri in self.rich_iters():
            self.assertEqual(list(ri.islice(2, 4)), [3, 4])
        for ri in self.rich_iters():
            self.assertEqual(list(ri.islice(1, None, 2)), [2, 4])

    def test_map(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.map(op.neg)), [-1, -2, -3, -4, -5])
        for ri in self.rich_iters():
            self.assertEqual(
                list(ri.map(pow, reversed(range(1, 6)))), [1, 16, 27, 16, 5]
            )

    def test_stapmap(self):
        iterable = list(zip(range(1, 6), reversed(range(1, 6))))
        for ri in self.rich_iters(iterable):
            self.assertEqual(list(ri.starmap(pow)), [1, 16, 27, 16, 5])

    def test_takewhile(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.takewhile(less_than_3)), [1, 2])

    def test_tee(self):
        for ri in self.rich_iters():
            it1, it2 = ri.tee()
            for i in it1, it2:
                self.assertIs(i.__class__, ri.__class__)
            self.assertEqual(list(it1), [1, 2, 3, 4, 5])
            self.assertEqual(list(it2), [1, 2, 3, 4, 5])
        for ri in self.rich_iters():
            it1, it2, it3 = ri.tee(3)
            for i in it1, it2, it3:
                self.assertIs(i.__class__, ri.__class__)
            self.assertEqual(list(it1), [1, 2, 3, 4, 5])
            self.assertEqual(list(it2), [1, 2, 3, 4, 5])
            self.assertEqual(list(it3), [1, 2, 3, 4, 5])

    def test_zip(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.zip('xy')), [(1, 'x'), (2, 'y')])
        for ri in self.rich_iters():
            self.assertEqual(
                list(ri.zip('xyz', [True, False])),
                [(1, 'x', True), (2, 'y', False)],
            )

    def test_zip_longest(self):
        for ri in self.rich_iters():
            self.assertEqual(
                list(ri.zip_longest('xy', fillvalue='')),
                [(1, 'x'), (2, 'y'), (3, ''), (4, ''), (5, '')],
            )
        for ri in self.rich_iters():
            self.assertEqual(
                list(ri.zip_longest('xyz', [True, False])),
                [
                    (1, 'x', True),
                    (2, 'y', False),
                    (3, 'z', None),
                    (4, None, None),
                    (5, None, None),
                ],
            )

    def test_product(self):
        for ri in self.rich_iters('ABCD'):
            self.assertEqual(
                list(ri.product('xy')),
                list(map(tuple, 'Ax Ay Bx By ' 'Cx Cy Dx Dy'.split())),
            )
        for ri in self.rich_iters(range(2)):
            self.assertEqual(
                list(ri.product(repeat=3)),
                [
                    (0, 0, 0),
                    (0, 0, 1),
                    (0, 1, 0),
                    (0, 1, 1),
                    (1, 0, 0),
                    (1, 0, 1),
                    (1, 1, 0),
                    (1, 1, 1),
                ],
            )

    def test_permutations(self):
        for ri in self.rich_iters('ABCD'):
            self.assertEqual(
                list(ri.permutations(2)),
                list(
                    map(
                        tuple, 'AB AC AD BA BC BD ' 'CA CB CD DA DB DC'.split()
                    )
                ),
            )
        for ri in self.rich_iters(range(3)):
            self.assertEqual(
                list(ri.permutations()),
                [
                    (0, 1, 2),
                    (0, 2, 1),
                    (1, 0, 2),
                    (1, 2, 0),
                    (2, 0, 1),
                    (2, 1, 0),
                ],
            )

    def test_combinations(self):
        for ri in self.rich_iters('ABCD'):
            self.assertEqual(
                list(ri.combinations(2)),
                [
                    ('A', 'B'),
                    ('A', 'C'),
                    ('A', 'D'),
                    ('B', 'C'),
                    ('B', 'D'),
                    ('C', 'D'),
                ],
            )
        for ri in self.rich_iters(range(4)):
            self.assertEqual(
                list(ri.combinations(3)),
                [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)],
            )

    def test_combinations_with_replacement(self):
        for ri in self.rich_iters('ABC'):
            self.assertEqual(
                list(ri.combinations_with_replacement(2)),
                [
                    ('A', 'A'),
                    ('A', 'B'),
                    ('A', 'C'),
                    ('B', 'B'),
                    ('B', 'C'),
                    ('C', 'C'),
                ],
            )

    def test_slots(self):
        for ri in self.rich_iters():
            with self.assertRaises(AttributeError):
                ri.foo = None

    def test_state_policy(self):
        for ri in self.rich_iters():
            self.assertIs(ri.state_policy, StatePolicy.SHARE)
        # iterating the mapped iterator exhausts the original one too
        for ri in self.rich_iters():
            ri2 = ri.map(op.neg)
            self.assertIsNot(ri, ri2)
            self.assertIs(ri2.__class__, ri.__class__)
            self.assertEqual(list(ri2), [-1, -2, -3, -4, -5])
            self.assertEqual(list(ri2), [])
            self.assertEqual(list(ri), [])
        # iterating the original iterator exhausts the mapped one too
        for ri in self.rich_iters():
            ri2 = ri.map(op.neg)
            self.assertIsNot(ri, ri2)
            self.assertIs(ri2.__class__, ri.__class__)
            self.assertEqual(list(ri), [1, 2, 3, 4, 5])
            self.assertEqual(list(ri), [])
            self.assertEqual(list(ri2), [])


class MagicIterTests(RichIterTests):
    iter_factory = magic_iter

    def test_get_index(self):
        for ri in self.rich_iters():
            self.assertEqual(ri[2], 3)
        for ri in self.rich_iters():
            with self.assertRaises(IndexError):
                ri[6]
        for ri in self.rich_iters():
            with self.assertRaises(ValueError):
                ri[-1]

    def test_get_slice(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri[:]), [1, 2, 3, 4, 5])
        for ri in self.rich_iters():
            self.assertEqual(list(ri[:2]), [1, 2])
        for ri in self.rich_iters():
            self.assertEqual(list(ri[2:]), [3, 4, 5])
        for ri in self.rich_iters():
            self.assertEqual(list(ri[2:4]), [3, 4])
        for ri in self.rich_iters():
            self.assertEqual(list(ri[1::2]), [2, 4])

    def test_add(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri + 'DEF'), [1, 2, 3, 4, 5, 'D', 'E', 'F'])

    def test_radd(self):
        for ri in self.rich_iters():
            self.assertEqual(list('DEF' + ri), ['D', 'E', 'F', 1, 2, 3, 4, 5])

    def test_or(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri | op.neg), [-1, -2, -3, -4, -5])

    def test_and(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri & is_odd), [1, 3, 5])

    def test_xor(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri ^ is_odd), [2, 4])

    def test_rshift(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri >> less_than_3), [3, 4, 5])

    def test_lshift(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri << less_than_3), [1, 2])

    def test_pow_iterable(self):
        for ri in self.rich_iters('ABCD'):
            self.assertEqual(
                list(ri ** 'xy'),
                list(map(tuple, 'Ax Ay Bx By ' 'Cx Cy Dx Dy'.split())),
            )

    def test_rpow_iterable(self):
        for ri in self.rich_iters('ABCD'):
            with self.assertRaises(TypeError):
                3 ** ri
            self.assertEqual(
                list('xy' ** ri),
                list(map(tuple, 'xA xB xC xD ' 'yA yB yC yD'.split())),
            )

    def test_pow_int(self):
        for ri in self.rich_iters(range(2)):
            self.assertEqual(
                list(ri ** 3),
                [
                    (0, 0, 0),
                    (0, 0, 1),
                    (0, 1, 0),
                    (0, 1, 1),
                    (1, 0, 0),
                    (1, 0, 1),
                    (1, 1, 0),
                    (1, 1, 1),
                ],
            )


class ShareRichIterTests(RichIterTests):
    state_policy = 'share'


class ShareMagicIterTests(MagicIterTests):
    state_policy = 'share'


class CopyRichIterTests(RichIterTests):
    state_policy = 'copy'

    def test_state_policy(self):
        for ri in self.rich_iters():
            self.assertIs(ri.state_policy, StatePolicy.COPY)
        # iterating the mapped iterator does not iterate the original one
        for ri in self.rich_iters():
            ri2 = ri.map(op.neg)
            self.assertIs(ri2.__class__, ri.__class__)
            self.assertEqual(list(ri2), [-1, -2, -3, -4, -5])
            self.assertEqual(list(ri2), [])
            self.assertEqual(list(ri), [1, 2, 3, 4, 5])
        # iterating the original iterator does not iterate the mapped one
        for ri in self.rich_iters():
            ri2 = ri.map(op.neg)
            self.assertIs(ri2.__class__, ri.__class__)
            self.assertEqual(list(ri), [1, 2, 3, 4, 5])
            self.assertEqual(list(ri), [])
            self.assertEqual(list(ri2), [-1, -2, -3, -4, -5])


class CopyMagicIterTests(CopyRichIterTests, MagicIterTests):
    iter_factory = magic_iter
    state_policy = 'copy'


class TransferRichIterTests(RichIterTests):
    state_policy = 'transfer'

    def test_state_policy(self):
        for ri in self.rich_iters():
            self.assertIs(ri.state_policy, StatePolicy.TRANSFER)
        # after generating a rich iterator from a 'transfer' rich iterator,
        # the latter can no longer be used
        for ri in self.rich_iters():
            ri2 = ri.map(op.neg)
            self.assertIs(ri2.__class__, ri.__class__)
            self.assertIteratorCannotBeUsed(ri)
            self.assertEqual(list(ri2), [-1, -2, -3, -4, -5])
            self.assertEqual(list(ri2), [])

    def assertIteratorCannotBeUsed(self, iterator):
        for func in (
            next,
            list,
            bool,
            copy.copy,
            op.methodcaller('map', op.neg),
            op.methodcaller('filter', is_odd),
            op.methodcaller('tee'),
            op.methodcaller('peek'),
        ):
            self.assertRaises(RuntimeError, func, iterator)


class TransferMagicIterTests(TransferRichIterTests, MagicIterTests):
    iter_factory = magic_iter
    state_policy = 'transfer'
