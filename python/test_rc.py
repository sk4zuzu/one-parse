import unittest
from textwrap import dedent as dd
from rc import RcParser

PARSE_AND_RENDER_TESTS = [
    dd('''
        export A=1
        S=2
        D=3
    '''),
    dd('''
        A='1'
        export S='2'
        D='3'
    '''),
    dd('''
        A="1"
        S="2"
        export D="3"
    '''),
    dd('''
        # A
            A=1

        export S='2' # S
        D="3"
         #D
    '''),
    dd('''
        A=1 #A
            export S='2 2' #S
         D="3 3" #D
    '''),
    dd('''
        A="1\\"2\\"3"
        S='1"2"3'
    '''),
    '  A=S',
    '  A=S  '
]

MATCH_AND_GET_TESTS = [{
    "input": dd('''
        A=1
        S=2
        D=3
    '''),
    "path": 'S',
    "match": ['S'],
    "value": None,
    "get": ['2']
},{
    "input": dd('''
        A=1
        S=2
        S=2
        D=3
    '''),
    "path": 'S',
    "match": ['S[1]', 'S[2]'],
    "value": None,
    "get": ['2', '2']
},{
    "input": dd('''
        A=1
        S=2
        S=3
    '''),
    "path": '*',
    "match": ['A', 'S[1]', 'S[2]'],
    "value": None,
    "get": ['1', '2', '3']
},{
    "input": dd('''
        A=1
        S=2
        S=3
    '''),
    "path": 'A[0]',
    "match": [],
    "value": None,
    "get": []
},{
    "input": dd('''
        A=1
        S=2
        S=3
        D=4
        D=5
    '''),
    "path": 'S[0]',
    "match": ['S[1]', 'S[2]'],
    "value": None,
    "get": ['2', '3']
},{
    "input": dd('''
        A=1
        S=2
        S=3
        D=4
        D=5
    '''),
    "path": '*[0]',
    "match": ['S[1]', 'S[2]', 'D[1]', 'D[2]'],
    "value": None,
    "get": ['2', '3', '4', '5']
},{
    "input": dd('''
        A=1
        S=2
        S=3
        D=4
        D=5
    '''),
    "path": '*[0]',
    "match": ['S[2]'],
    "value": '3',
    "get": ['2', '3', '4', '5']
}]

PUT_TESTS = [{
    "input": dd('''
    '''),
    "path": 'A',
    "value": '1',
    "put": dd('''
        A=1
    ''')
},{
    "input": dd('''
        A=1
    '''),
    "path": 'S',
    "value": '2',
    "put": dd('''
        A=1
        S=2
    ''')
},{
    "input": dd('''
        A=1
        S=2
    '''),
    "path": 'S',
    "value": '3',
    "put": dd('''
        A=1
        S=3
    ''')
},{
    "input": dd('''
        A=1
    '''),
    "path": 'A[0]',
    "value": '2',
    "put": dd('''
        A=1
        A=2
    ''')
},{
    "input": dd('''
        A=1
        S=2
    '''),
    "path": 'S[0]',
    "value": '3',
    "put": dd('''
        A=1
        S=2
        S=3
    ''')
},{
    "input": dd('''
        A=1
        S=2 # ASD
        # DSA
    '''),
    "path": 'S[0]',
    "value": '3',
    "put": dd('''
        A=1
        S=2 # ASD
        # DSA
        S=3
    ''')
},{
    "input": dd('''
        A=1
    '''),
    "path": 'S',
    "value": '',
    "put": dd('''
        A=1
        S=
    ''')
}]

DROP_TESTS = [{
    "input": dd('''
        A=1
        S=2
        D=3
    '''),
    "path": 'S',
    "value": None,
    "drop": dd('''
        A=1
        D=3
    ''')
},{
    "input": dd('''
        A=1
        S=2
        D=3
        export S=4
    '''),
    "path": 'S',
    "value": None,
    "drop": dd('''
        A=1
        D=3
    ''')
},{
    "input": dd('''
        A=1
        S=2
        D=3
        export S=4
    '''),
    "path": 'S[1]',
    "value": None,
    "drop": dd('''
        A=1
        D=3
        export S=4
    ''')
},{
    "input": dd('''
        A=1
        S=2
        D=3
        export S=4
    '''),
    "path": 'S[2]',
    "value": None,
    "drop": dd('''
        A=1
        S=2
        D=3
    ''')
}]

class TestRc(unittest.TestCase):
    def test_ParseAndRender(self):
        for inp in PARSE_AND_RENDER_TESTS:
            rc = RcParser(inp)
            rc.parse()
            self.assertEqual(rc.render(), inp)

    def test_MatchAndGet(self):
        for d in MATCH_AND_GET_TESTS:
            rc = RcParser(d['input'])
            rc.parse()
            self.assertEqual(rc.match(d['path'], d['value']), d['match'])
            self.assertEqual(rc.get(d['path']), d['get'])

    def test_Put(self):
        for d in PUT_TESTS:
            rc = RcParser(d['input'])
            rc.parse()
            rc.put(d['path'], d['value'])
            self.assertEqual(rc.render(), d['put'])

    def test_Drop(self):
        for d in DROP_TESTS:
            rc = RcParser(d['input'])
            rc.parse()
            rc.drop(d['path'], d['value'])
            self.assertEqual(rc.render(), d['drop'])

if __name__ == '__main__':
    unittest.main()
