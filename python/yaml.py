import io
from base import ParserBase

class YamlParser(ParserBase):
    def parser_proc(self):
        raise NotImplementedError

    def __init__(self, inp):
        super().__init__(inp)
        from ruamel.yaml import YAML
        self.yaml = YAML(typ='rt', pure=True)
        self.yaml.preserve_quotes = True

    def parse(self):
        self.parsed = self.yaml.load(self._inp)
        return self.parsed

    def render(self, node=None):
        b = io.BytesIO()
        self.yaml.dump(self.parsed, b)
        return b.getvalue().decode('utf-8')

    def match(self, path, value=None):
        raise NotImplementedError

    def get(self, path):
        rest = self._ypath(path, wildcards=None)
        v = self.parsed
        for k in rest:
            if isinstance(k, str):
                if not isinstance(v, dict):
                    return []
                try:
                    v = v[k]
                except KeyError:
                    return []
            elif isinstance(k, int):
                if not isinstance(v, list):
                    return []
                if k >= 1:
                    try:
                        v = v[k - 1]
                    except IndexError:
                        return []
                else:
                    raise self.InvalidPath
            else:
                raise self.InvalidPath
        return [v]

    def put(self, path, value):
        rest = self._ypath(path, wildcards=None)
        last = rest[-1]
        # a s d f g _    a s d f g     v      v      v      v      v
        #             =>           => (a, s) (s, d) (d, f) (f, g) (g, h)
        # _ s d f g h    s d f g h        ^      ^      ^      ^      ^
        v = self.parsed
        for (p, n) in zip(rest[:-1], rest[+1:]):
            if isinstance(p, str):
                if not isinstance(v, dict):
                    raise self.EmptyMatch
                try:
                    v = v[p]
                except KeyError:
                    if isinstance(n, str):
                        v[p] = dict()
                        v = v[p]
                    elif isinstance(n, int):
                        v[p] = list()
                        v = v[p]
                    else:
                        raise self.InvalidPath
            elif isinstance(p, int):
                if not isinstance(v, list):
                    raise self.EmptyMatch
                if p >= 1:
                    try:
                        v = v[p - 1]
                    except IndexError:
                        raise self.EmptyMatch
                elif p == 0:
                    if isinstance(n, str):
                        t = dict()
                        v.append(t)
                        v = t
                    elif isinstance(n, int):
                        t = list()
                        v.append(t)
                        v = t
                    else:
                        raise self.InvalidPath
                else:
                    raise self.InvalidPath
            else:
                raise self.InvalidPath
        # set the final value
        if isinstance(last, str):
            if not isinstance(v, dict):
                raise self.EmptyMatch
            v[last] = value
        elif isinstance(last, int):
            if not isinstance(v, list):
                raise self.EmptyMatch
            if last >= 1:
                try:
                    v[last - 1] = value
                except IndexError:
                    raise self.EmptyMatch
            elif last == 0:
                v.append(value)
            else:
                raise self.InvalidPath
        else:
            raise self.InvalidPath

    def drop(self, path, value=None):
        if value is not None:
            raise NotImplementedError
        rest = self._ypath(path, wildcards=None)
        last = rest.pop()
        v = self.parsed
        for k in rest:
            if isinstance(k, str):
                if not isinstance(v, dict):
                    return []
                try:
                    v = v[k]
                except KeyError:
                    raise self.EmptyMatch
            elif isinstance(k, int):
                if not isinstance(v, list):
                    return []
                if k >= 1:
                    try:
                        v = v[k - 1]
                    except IndexError:
                        raise self.EmptyMatch
                else:
                    raise self.InvalidPath
            else:
                raise self.InvalidPath
        # remove the final key/index
        if isinstance(last, str):
            if not isinstance(v, dict):
                raise self.EmptyMatch
            try:
                del v[last]
            except KeyError:
                raise self.EmptyMatch
        elif isinstance(last, int):
            if not isinstance(v, list):
                raise self.EmptyMatch
            if last >= 1:
                try:
                    del v[last - 1]
                except IndexError:
                    raise self.EmptyMatch
            else:
                raise self.InvalidPath
        else:
            raise self.InvalidPath

    def _ypath(self, path, wildcards=True):
        if wildcards is not None:
            raise NotImplementedError
        if not isinstance(path, list) or not path:
            raise self.InvalidPath
        return path

    def _searchable(self, node=None):
        raise NotImplementedError

    def _filtered(self, node=None, patterns=None, indices=None):
        raise NotImplementedError
