import re
from base import ParserBase

class RcParser(ParserBase):
    def parser_proc(self):
        def single_quoted():
            return self.between(lambda: self.take_exact("'"),
                                lambda: self.take_exact("'"),
                                lambda: "'" + self.take_while(lambda c: c != "'") + "'")

        def double_quoted():
            def pred(c):
                if c == '\\' or (c == '"' and pred.__dict__['escaped']):
                    pred.__dict__['escaped'] = not pred.__dict__['escaped']
                    return True
                else:
                    return c != '"'
            pred.__dict__['escaped'] = False
            return self.between(lambda: self.take_exact('"'),
                                lambda: self.take_exact('"'),
                                lambda: '"' + self.take_while(pred) + '"')

        def unquoted():
            def pred(c):
                return not (c == '#' or c.isspace())
            return self.take_while(pred) if pred(self.peek()) else self.quit()

        def attribute():
            return self.take_while(lambda c: c == '_' or c.isalnum())

        def blank():
            return self.take_while(lambda c: c in [' ', '\t'])

        def eol():
            return self.take_exact('\n')

        def blank_eol():
            return blank() + eol()

        def comment():
            return self.Comment.from_str(
                blank() + self.take_exact('#')
                        + self.take_while(lambda c: c != '\n')
                        + eol()
            )

        def pair():
            return self.Pair.from_args(
                self.one_of(lambda: blank() + self.take_exact('export') + blank(),
                            blank),
                attribute(),
                self.take_exact('='),
                self.one_of(single_quoted,
                            double_quoted,
                            unquoted,
                            blank),
                self.one_of(comment,
                            blank_eol,
                            blank)
            )

        return self.Sequence.from_args(
            *(self.zero_or_more(lambda: self.one_of(pair,
                                                    comment,
                                                    blank_eol)))
        )

    def __init__(self, inp):
        super().__init__(inp)

    def render(self, node=None):
        acc = ''
        for v in (node or self.parsed):
            if isinstance(v, str):
                acc += v
            elif isinstance(v, self.Pair):
                acc += ''.join(v)
            else:
                raise self.InvalidTree
        return acc

    # due to overwhelming complexity we decided not to use recurrence here.. xD
    def put(self, path, value):
        atrb, atrb_i, _, _ = self._ypath(path, wildcards=False)
        s = self._searchable()

        # add a new pair directly at the root level
        if s.get(atrb) is None or (atrb_i is not None and atrb_i == 0):
            self.parsed.append(self.Pair.from_args(
                '', atrb, '=', str(value), '\n'
            ))

        # require paths to be unequivocal
        elif atrb_i is None and len(s[atrb]) > 1:
            raise self.AmbiguousMatch

        # fail when nothing found
        elif s.get(atrb) is None or (s := s[atrb][0 if atrb_i is None else (atrb_i - 1)]) is None:
            raise self.EmptyMatch

        # the pattern must resolve into a pair
        elif not isinstance(s, self.Pair):
            raise self.InvalidPath

        # update the value (root level)
        else:
            s[3] = str(value)

    def drop(self, path, value=None):
        atrb, atrb_i, _, _ = self._ypath(path, wildcards=True)
        def recurse(node):
            if isinstance(node, self.Pair) and (value is None or node[3] == str(value)):
                for i, x in enumerate(self.parsed):
                    if id(x) == id(node):
                        self.parsed.pop(i)
                        break
            elif isinstance(node, self.Sequence):
                for v in node:
                    recurse(v)
            elif isinstance(node, self.Lookup):
                for v in node.values():
                    recurse(v)
        recurse(self._filtered(patterns=[atrb, None], indices=[atrb_i, None]))

    def _ypath(self, path, wildcards=True):
        wild = '*' if wildcards else ''
        regx = rf'''(?x)
            ^
            ( [A-Za-z0-9_{wild}]+ )
            (?:
                \[ ( [0-9]* ) \]
            )?
            $
        '''
        if (m := re.match(regx, path)) is None:
            raise self.InvalidPath

        atrb   = m[1]
        atrb_i = None if len(m[2] or '') == 0 else int(m[2])
        if atrb is None or (atrb_i is not None and int(atrb_i) < 0):
            raise self.InvalidPath

        return atrb, atrb_i, None, None

    def _searchable(self, node=None):
        def recurse(node, index):
            if isinstance(node, self.Pair):
                node.setm('_index_', index)
            elif isinstance(node, self.Sequence):
                for i, v in enumerate(node):
                    recurse(v, (i + 1) if (len(node) > 1) else None)
            elif isinstance(node, self.Lookup):
                node.setm('_index_', index)
                for v in node.values():
                    recurse(v, None)
        acc = self.Lookup()
        for v in (node or self.parsed):
            if isinstance(v, self.Pair):
                acc[v[1]] = acc.get(v[1], self.Sequence())
                acc[v[1]].append(v)
        recurse(acc, None)
        return acc
