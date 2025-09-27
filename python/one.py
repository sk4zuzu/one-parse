import copy
import re
from base import ParserBase

class OneParser(ParserBase):
    class Vector(ParserBase.Sequence): pass

    def parser_proc(self):
        def quoted():
            escaped = [False]
            def pred(c):
                if c == '\\' or (c == '"' and escaped[0]):
                    escaped[0] = not escaped[0]
                    return True
                else:
                    return c != '"'
            return self.between(lambda: self.take_exact('"'),
                                lambda: self.take_exact('"'),
                                lambda: '"' + self.take_while(pred) + '"')

        def unquoted():
            def pred(c):
                return not (c in [']', '[', '"', ',', '#'] or c.isspace())
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
                blank(),
                attribute(),
                blank() + self.take_exact('=') + blank(),
                self.one_of(quoted,
                            unquoted),
                self.one_of(comment,
                            blank_eol,
                            blank)
            )

        def blank_comma():
            t = blank(); self.take_exact(',')
            return t

        def item():
            return self.Pair.from_args(
                blank(),
                attribute(),
                blank() + self.take_exact('=') + blank(),
                self.one_of(quoted,
                            unquoted),
                self.one_of(lambda: self.Comment.from_str(blank_comma() + comment()),
                            lambda: blank_comma() + blank_eol(),
                            blank_comma,
                            comment,
                            blank_eol,
                            blank)
            )

        def vector():
            return self.Vector.from_args(
                blank(),
                attribute(),
                blank() + self.take_exact('=') + blank(),
                self.between(lambda: self.take_exact('['),
                             lambda: self.take_exact(']'),
                             lambda: self.Sequence.from_args(
                            *(self.zero_or_more(lambda: self.one_of(item,
                                                                    comment,
                                                                    blank_eol)))
                        )
                ),
                self.one_of(comment,
                            blank_eol,
                            blank)
            )

        return self.Sequence.from_args(
            *(self.zero_or_more(lambda: self.one_of(pair,
                                                    vector,
                                                    comment,
                                                    blank_eol)))
        )

    def __init__(self, inp):
        super().__init__(inp)

    def render(self, node=None):
        acc = ''
        for vv in (node or self.parsed):
            if isinstance(vv, str):
                acc += vv
            elif isinstance(vv, self.Pair):
                acc += ''.join(vv)
            elif isinstance(vv, self.Vector):
                acc += ''.join(vv[0:3])
                acc += '['
                count = 0
                for v in vv[3]:
                    if isinstance(v, self.Pair):
                        count += 1
                for v in vv[3]:
                    if isinstance(v, str):
                        acc += v
                    elif isinstance(v, self.Pair):
                        acc += ''.join(v[0:4])
                        count = count - 1
                        if count > 0:
                            acc += ','
                        acc += v[4]
                    else:
                        raise self.InvalidTree
                acc += ']'
                acc += vv[4]
            else:
                raise self.InvalidTree
        return acc

    def put(self, path, value):
        atrb, atrb_i, item, item_i = self._ypath(path, wildcards=False)
        s = self._searchable()

        # add a new pair directly at the root level
        if (s.get(atrb) is None or (atrb_i is not None and atrb_i == 0)) and item is None:
            self.parsed.append(self.Pair.from_args(
                '', atrb, ' = ', str(value), '\n'
            ))
            return

        # add a new vector with a single pair directly at the root level
        if (s.get(atrb) is None or (atrb_i is not None and atrb_i == 0)) and item is not None:
            self.parsed.append(self.Vector.from_args(
                '', atrb, ' = ', self.Sequence.from_args(
                    '\n', self.Pair.from_args(
                        ' ', item, ' = ', str(value), ' '
                    )
                ), '\n'
            ))
            return

        # require paths to be unequivocal
        if atrb_i is None and len(s[atrb]) > 1:
            raise self.AmbiguousMatch

        # fail when nothing found
        try:
            s = s[atrb][0 if atrb_i is None else (atrb_i - 1)]
        except (KeyError, IndexError):
            raise self.EmptyMatch

        # when second pattern is provided then first one must not resolve into a pair
        # when second pattern is not provided then first one must resolve into a pair
        if (item is None) ^ isinstance(s, self.Pair):
            raise self.InvalidPath

        # update the value (root level)
        if item is None:
            s[3] = str(value)
            return

        # add a new pair to an existing vector
        if s.get(item) is None or (item_i is not None and item_i == 0):
            parent = s[list(s.keys())[0]][0].getm('_parent_') # get parent from a neighbor pair
            indent = self.__infer_vector_indent(parent)
            # apply suffix correction to the former last pair
            indent['prev_pair'][4] = indent['prev_suffix']
            # append new correctly indented pair
            parent.append(self.Pair.from_args(
                indent['next_prefix'], item, ' = ', str(value), indent['next_suffix']
            ))
            return

        # require paths to be unequivocal
        if item_i is None and len(s[item]) > 1:
            raise self.AmbiguousMatch

        # fail when nothing found
        try:
            s = s[item][0 if item_i is None else (item_i - 1)]
        except (KeyError, IndexError):
            raise self.EmptyMatch

        # second pattern must resolve into a pair
        if not isinstance(s, self.Pair):
            raise self.InvalidPath

        # update the value (vector level)
        s[3] = str(value)
        return

    def drop(self, path, value=None):
        atrb, atrb_i, item, item_i = self._ypath(path, wildcards=True)
        def recurse(node):
            if isinstance(node, self.Pair) and (value is None or node[3] == str(value)):
                parent = node.getm('_parent_')
                for i, x in enumerate(parent):
                    if id(x) == id(node):
                        parent.pop(i)
                        break
            elif isinstance(node, self.Sequence):
                for v in node:
                    recurse(v)
            elif isinstance(node, self.Lookup):
                for v in node.values():
                    recurse(v)
        recurse(self._filtered(patterns=[atrb, item], indices=[atrb_i, item_i]))
        # remove empty vectors
        for node in self.parsed:
            if isinstance(node, self.Vector) and not [v for v in node[3] if isinstance(v, self.Pair)]:
                for i, x in enumerate(self.parsed):
                    if id(x) == id(node):
                        self.parsed.pop(i)
                        break

    def _ypath(self, path, wildcards=True):
        if isinstance(path, list):
            path = '/'.join(path)
        wild = '*' if wildcards else ''
        regx = rf'''(?x)
            ^
            ( [A-Za-z0-9_{wild}]+ )
            (?:
                \[ ( [0-9]* ) \]
            )?
            (?:
                /
                ( [A-Za-z0-9_{wild}]+ )
                (?:
                    \[ ( [0-9]* ) \]
                )?
            )?
            $
        '''
        m = re.match(regx, path)
        if m is None:
            raise self.InvalidPath

        atrb   = m[1]
        atrb_i = None if len(m[2] or '') == 0 else int(m[2])
        item   = m[3]
        item_i = None if len(m[4] or '') == 0 else int(m[4])
        if atrb is None or (item is None and item_i is not None) \
                        or (atrb_i is not None and int(atrb_i) < 0) \
                        or (item_i is not None and int(item_i) < 0):
            raise self.InvalidPath

        return atrb, atrb_i, item, item_i

    def _searchable(self, node=None):
        def recurse1(node):
            acc = self.Lookup()
            for v in node:
                if isinstance(v, self.Pair):
                    acc[v[1]] = acc.get(v[1], self.Sequence())
                    acc[v[1]].append(v)
                    v.setm('_parent_', node)
                elif isinstance(v, self.Vector):
                    acc[v[1]] = acc.get(v[1], self.Sequence())
                    acc[v[1]].append(recurse1(v[3]))
            return acc
        def recurse2(node, index):
            if isinstance(node, self.Pair):
                node.setm('_index_', index)
            elif isinstance(node, self.Sequence):
                for i, v in enumerate(node):
                    recurse2(v, (i + 1) if (len(node) > 1) else None)
            elif isinstance(node, self.Lookup):
                node.setm('_index_', index)
                for v in node.values():
                    recurse2(v, None)
            return node
        return recurse2(recurse1(node or self.parsed), None)

    def __infer_vector_indent(self, parent):
        acc = { 'has_eol': False,
                'prev_pair': None,
                'next_prefix': '',
                'prev_suffix': '',
                'next_suffix': '' }
        for node in parent:
            if isinstance(node, str):
                if '\n' in node:
                    acc['has_eol'] = True
            elif isinstance(node, self.Pair):
                if '\n' in node[4]:
                    acc['has_eol'] = True
                acc['prev_pair'] = node
        acc['next_prefix'] = copy.copy(acc['prev_pair'][0])
        s = acc['prev_pair'][4]
        if isinstance(s, self.Comment):
            acc['prev_suffix'] = copy.copy(s)
            acc['next_suffix'] = ' '
        else:
            acc['prev_suffix'] = '\n' if acc['has_eol'] else ''
            acc['next_suffix'] = copy.copy(s)
        return acc
