import copy
import fnmatch
from engine import ParserEngine

class ParserBase(ParserEngine):
    class InvalidPath(Exception): pass
    class InvalidTree(Exception): pass
    class AmbiguousMatch(Exception): pass
    class EmptyMatch(Exception): pass

    class Meta:
        def setm(self, k, v): self.__dict__[k] = v; return self
        def getm(self, k): return self.__dict__[k]

    class Lookup(Meta, dict):
        @classmethod
        def from_args(cls, *a): return cls(a)

    class Sequence(Meta, list):
        @classmethod
        def from_args(cls, *a): return cls(a)

    class Pair(Sequence):
        @classmethod
        def from_args(cls, *a): return cls(a)

    class Comment(Meta, str):
        @classmethod
        def from_str(cls, s): return cls(s) if ('#' in s) else str(s)

    def __init__(self, inp):
        super().__init__(inp)

    def parse(self):
        self.parsed = self.parser_proc()
        if len(self._input()) > 0:
            line = self._inp[0:self._pos].count('\n') + 1
            text = self._inp[self._pos:(self._pos + 16)].split('\n', 1)[0]
            raise self.ParseFailure(f"line {line}, at `{text}..'")
        return self.parsed

    def render(self, node=None):
        raise NotImplementedError

    def match(self, path, value=None):
        atrb, atrb_i, item, item_i = self._ypath(path, wildcards=True)
        def recurse(node, pfx, acc):
            if isinstance(node, self.Pair) and (value is None or node[3] == str(value)):
                idx = '' if (i := node.getm('_index_')) is None else f'[{i}]'
                acc.append(pfx + idx)
            elif isinstance(node, self.Sequence):
                for v in node:
                    recurse(v, pfx, acc)
            elif isinstance(node, self.Lookup):
                if len(pfx) > 0:
                    idx = '' if (i := node.getm('_index_')) is None else f'[{i}]'
                    pfx += idx + '/'
                for k, v in node.items():
                    recurse(v, pfx + k, acc)
        recurse(self._filtered(patterns=[atrb, item], indices=[atrb_i, item_i]), '', (found := []))
        return found

    def get(self, path):
        atrb, atrb_i, item, item_i = self._ypath(path, wildcards=True)
        def recurse(node, acc):
            if isinstance(node, self.Pair):
                acc.append(node[3])
            elif isinstance(node, self.Sequence):
                for v in node:
                    recurse(v, acc)
            elif isinstance(node, self.Lookup):
                for v in node.values():
                    recurse(v, acc)
        recurse(self._filtered(patterns=[atrb, item], indices=[atrb_i, item_i]), (found := []))
        return found

    def put(self, path, value):
        raise NotImplementedError

    def drop(self, path, value=None):
        raise NotImplementedError

    def _ypath(self, path, wildcards=True):
        raise NotImplementedError

    def _searchable(self, node=None):
        raise NotImplementedError

    def _filtered(self, node=None, patterns=None, indices=None):
        def recurse(node, patterns, indices):
            if isinstance(node, self.Pair) and len(patterns) == 0:
                return node
            elif isinstance(node, self.Lookup):
                try:
                    pat = patterns.pop(0)
                except IndexError:
                    pat = None
                if pat is not None:
                    acc = {}
                    for k, vv in node.items():
                        if fnmatch.fnmatch(k, pat):
                            v = recurse(vv, copy.copy(patterns), copy.copy(indices))
                            if v is not None:
                                acc[k] = v
                    if acc:
                        return self.Lookup(acc).setm('_index_', node.getm('_index_'))
            elif isinstance(node, self.Sequence):
                try:
                    idx = indices.pop(0)
                except IndexError:
                    idx = None
                if idx is None or (idx == 0 and len(node) > 1):
                    acc = []
                    for vv in node:
                        v = recurse(vv, copy.copy(patterns), copy.copy(indices))
                        if v is not None:
                            acc.append(v)
                    if acc := [x for x in acc if x is not None]:
                        return self.Sequence(acc)
                elif idx is not None and idx != 0 and len(node) > 1 and (vv := node[idx - 1]) is not None:
                    v = recurse(vv, copy.copy(patterns), copy.copy(indices))
                    if v is not None:
                        return self.Sequence([v])
        return recurse(
            self._searchable(node or self.parsed),
            [x for x in copy.copy(patterns or []) if x is not None],
            copy.copy(indices or [])
        )
