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


class rich_iter_chain:

    __slots__ = ("_ri",)

    def __init__(self, rich_iterator):
        self._ri = rich_iterator

    def __call__(self, *iterables):
        return self._ri._chain(*iterables)

    def from_iterable(self):
        return self._ri._chain_from_iterable()


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

    @classmethod
    def add_method(cls, wrapped, *, name=None, it_index=0, preserve_cls=True):
        if name is None:
            name = wrapped.__name__

        def wrapper(self, *args, **kwargs):
            if self.state_policy is StatePolicy.COPY:
                self._it, iterator = it.tee(self._it)
            else:
                iterator = self._it
            args = list(args)
            args.insert(it_index, iterator)
            new_iterator = wrapped(*args, **kwargs)
            if self.state_policy is StatePolicy.TRANSFER:
                self._it = UnusableIterator()
            if preserve_cls:
                new_iterator = self.__class__(new_iterator, self.state_policy)
            return new_iterator

        wrapper.__wrapped__ = wrapped
        wrapper.__name__ = name
        wrapper.__qualname__ = f"{cls.__name__}.{name}"
        wrapper.__doc__ = wrapped.__doc__
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

        setattr(cls, name, wrapper)

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

    def groupby(self, key=None):
        return (
            (k, self.__class__(g, self.state_policy))
            for k, g in self._groupby(key)
        )

    chain = property(rich_iter_chain)


rich_iter.add_method(it.chain, name="_chain")
rich_iter.add_method(it.chain.from_iterable, name="_chain_from_iterable")
rich_iter.add_method(it.groupby, name="_groupby")
rich_iter.add_method(it.accumulate)
rich_iter.add_method(it.compress)
rich_iter.add_method(it.cycle)
rich_iter.add_method(it.dropwhile, it_index=1)
rich_iter.add_method(enumerate)
rich_iter.add_method(filter, it_index=1)
rich_iter.add_method(it.filterfalse, it_index=1)
rich_iter.add_method(it.islice)
rich_iter.add_method(map, it_index=1)
rich_iter.add_method(functools.reduce, it_index=1, preserve_cls=False)
rich_iter.add_method(it.starmap, it_index=1)
rich_iter.add_method(sum, preserve_cls=False)
rich_iter.add_method(it.takewhile, it_index=1)
rich_iter.add_method(zip)
rich_iter.add_method(it.zip_longest)
rich_iter.add_method(it.product)
rich_iter.add_method(it.permutations)
rich_iter.add_method(it.combinations)
rich_iter.add_method(it.combinations_with_replacement)
