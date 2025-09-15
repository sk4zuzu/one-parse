class ParserEngine:
    class ParseFailure(Exception): pass

    def __init__(self, inp):
        self._inp = inp
        self._pos = 0

    def zero_or_more(self, parser):
        try:
            matches = []
            while True:
                matches.append(self.__backtrack(parser))
        except self.ParseFailure:
            return matches

    def one_of(self, *parsers):
        for parser in parsers:
            try:
                return self.__backtrack(parser)
            except self.ParseFailure:
                pass
        self.quit()

    def between(self, begin, end, inner):
        def block():
            begin(); t = inner(); end()
            return t
        return self.__backtrack(block)

    def peek(self, length=1):
        return s if len(s := self._input()[0:length]) == length else self.quit()

    def take(self, length=1):
        t = self.peek(length); self.__consume(length)
        return t

    def take_exact(self, pattern):
        def block():
            return s if (s := self.take(len(pattern))) == pattern else self.quit()
        return self.__backtrack(block)

    def take_while(self, pred):
        try:
            s = ''
            def block():
                return c if pred(c := self.take()) else self.quit()
            while True:
                s += self.__backtrack(block)
            return s
        except self.ParseFailure:
            return s

    def quit(self):
        raise self.ParseFailure

    def _input(self):
        return self._inp[self._pos:]

    def __consume(self, length=1):
        self._pos += length

    def __backtrack(self, parser):
        try:
            before = self._pos
            return parser()
        except self.ParseFailure as e:
            self._pos = before
            raise e
