import functools
import inspect
import itertools as it
from enum import Enum

__all__ = ["rich_iter", "StatePolicy"]


_UNDEFINED = object()


class StatePolicy(Enum):
    SHARE = "share"
    COPY = "copy"
    TRANSFER = "transfer"


class UnusableIterator:
    def _runtime_error(*_):
        raise RuntimeError("iterator can no longer be used")

    __iter__ = __next__ = __bool__ = __getattr__ = _runtime_error
    del _runtime_error


def wrap_as_method(
    wrapped, *, it_index=0, preserve_cls=True, unusable_it=UnusableIterator()
):
    @functools.wraps(
        wrapped, assigned=('__name__', '__qualname__', '__doc__'), updated=()
    )
    def wrapper(self, *args, **kwargs):
        if self.state_policy is StatePolicy.COPY:
            self._it, iterator = it.tee(self._it)
        else:
            iterator = self._it
        args = list(args)
        args.insert(it_index, iterator)
        new_iterator = wrapped(*args, **kwargs)
        if self.state_policy is StatePolicy.TRANSFER:
            self._it = unusable_it
        if preserve_cls:
            new_iterator = self.__class__(new_iterator, self.state_policy)
        return new_iterator

    try:
        wrapper_parameters = [
            inspect.Parameter("self", inspect.Parameter.POSITIONAL_ONLY)
        ]
        wrapper_parameters.extend(
            param
            for i, param in enumerate(
                inspect.signature(wrapped).parameters.values()
            )
            if i != it_index
        )
        wrapper.__signature__ = inspect.Signature(wrapper_parameters)
    except ValueError:
        pass
    return wrapper


class rich_iter_chain:

    __slots__ = ("_ri",)
    _chain = staticmethod(wrap_as_method(it.chain))
    _chain_from_iterable = staticmethod(wrap_as_method(it.chain.from_iterable))

    def __init__(self, rich_iterator):
        self._ri = rich_iterator

    def __call__(self, *iterables):
        return self._chain(self._ri, *iterables)

    def from_iterable(self):
        return self._chain_from_iterable(self._ri)


class rich_iter:
    __slots__ = ("state_policy", "_it", "_peeked")

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
    def groupby(self, key=None):
        return (
            (k, self.__class__(g, self.state_policy))
            for k, g in self._groupby(key)
        )

    _groupby = wrap_as_method(it.groupby)
    accumulate = wrap_as_method(it.accumulate)
    chain = property(rich_iter_chain)
    compress = wrap_as_method(it.compress)
    cycle = wrap_as_method(it.cycle)
    dropwhile = wrap_as_method(it.dropwhile, it_index=1)
    enumerate = wrap_as_method(enumerate)
    filter = wrap_as_method(filter, it_index=1)
    filterfalse = wrap_as_method(it.filterfalse, it_index=1)
    islice = wrap_as_method(it.islice)
    map = wrap_as_method(map, it_index=1)
    reduce = wrap_as_method(functools.reduce, it_index=1, preserve_cls=False)
    starmap = wrap_as_method(it.starmap, it_index=1)
    sum = wrap_as_method(sum, preserve_cls=False)
    takewhile = wrap_as_method(it.takewhile, it_index=1)
    zip = wrap_as_method(zip)
    zip_longest = wrap_as_method(it.zip_longest)
    product = wrap_as_method(it.product)
    permutations = wrap_as_method(it.permutations)
    combinations = wrap_as_method(it.combinations)
    combinations_with_replacement = wrap_as_method(
        it.combinations_with_replacement
    )
