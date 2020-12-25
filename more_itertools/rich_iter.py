import functools
import itertools as it
from enum import Enum

__all__ = ['rich_iter', 'StatePolicy']


_UNDEFINED = object()


class StatePolicy(Enum):
    SHARE = "share"
    COPY = "copy"
    TRANSFER = "transfer"


class UnusableIterator:
    def _runtime_error(*_):
        raise RuntimeError('iterator can no longer be used')

    __iter__ = __next__ = __bool__ = __getitem__ = __getattr__ = _runtime_error
    del _runtime_error


def wrap_itertools_func(func, it_index=0, unusable_it=UnusableIterator()):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.state_policy is StatePolicy.COPY:
            self._it, iterator = it.tee(self._it)
        else:
            iterator = self._it
        args = list(args)
        args.insert(it_index, iterator)
        new_iterator = func(*args, **kwargs)
        if self.state_policy is StatePolicy.TRANSFER:
            self._it = unusable_it
        return self.__class__(new_iterator, self.state_policy)

    return wrapper


class rich_iter:
    __slots__ = ('state_policy', '_it', '_peeked')

    def __init__(self, iterable, state_policy=StatePolicy.SHARE):
        self.state_policy = StatePolicy(state_policy)
        self._it = iter(iterable)

    @classmethod
    def count(cls, start=0, step=1, *, state_policy=StatePolicy.SHARE):
        i = it.count(start, step)
        return cls(i, state_policy=state_policy)

    @classmethod
    def repeat(cls, obj, times=None, *, state_policy=StatePolicy.SHARE):
        i = it.repeat(obj, times) if times is not None else it.repeat(obj)
        return cls(i, state_policy=state_policy)

    def tee(self, n=2):
        return tuple(
            self.__class__(iterator, self.state_policy)
            for iterator in it.tee(self._it, n)
        )

    def peek(self, default=_UNDEFINED):
        try:
            return self._peeked
        except AttributeError:
            try:
                self._peeked = next(self._it)
                return self._peeked
            except StopIteration:
                if default is _UNDEFINED:
                    raise
                return default

    def __iter__(self):
        return self

    def __next__(self):
        peeked = getattr(self, "_peeked", _UNDEFINED)
        if peeked is _UNDEFINED:
            peeked = next(self._it)
        else:
            del self._peeked
        return peeked

    def __bool__(self):
        try:
            self.peek()
        except StopIteration:
            return False
        return True

    def __copy__(self):
        self._it, new_it = it.tee(self._it)
        return self.__class__(new_it, self.state_policy)

    # wrapped itertools functions
    accumulate = wrap_itertools_func(it.accumulate)
    chain = wrap_itertools_func(it.chain)
    chain_from_iterable = wrap_itertools_func(it.chain.from_iterable)
    compress = wrap_itertools_func(it.compress)
    cycle = wrap_itertools_func(it.cycle)
    dropwhile = wrap_itertools_func(it.dropwhile, it_index=1)
    filter = wrap_itertools_func(filter, it_index=1)
    filterfalse = wrap_itertools_func(it.filterfalse, it_index=1)
    groupby = wrap_itertools_func(it.groupby)
    islice = wrap_itertools_func(it.islice)
    map = wrap_itertools_func(map, it_index=1)
    starmap = wrap_itertools_func(it.starmap, it_index=1)
    takewhile = wrap_itertools_func(it.takewhile, it_index=1)
    zip = wrap_itertools_func(zip)
    zip_longest = wrap_itertools_func(it.zip_longest)
    product = wrap_itertools_func(it.product)
    permutations = wrap_itertools_func(it.permutations)
    combinations = wrap_itertools_func(it.combinations)
    combinations_with_replacement = wrap_itertools_func(
        it.combinations_with_replacement
    )
