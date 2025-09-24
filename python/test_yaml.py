import unittest
from textwrap import dedent
from yaml import YamlParser

def dd(inp):
    return dedent(inp).lstrip('\n')

PARSE_AND_RENDER_TESTS = [
    dd('''
        a:
          s:
            d: "3"
    '''),
    dd('''
        a: 1
        s: 2
        d: 3
    '''),
    dd('''
        a: '1'
        s: '2'
        d: '3'
    '''),
    dd('''
        a: "1"
        s: "2"
        d: "3"
    '''),
    dd('''
        # a
        a: 1

        s: '2' # s
        d: "3"
         #d
    '''),
    dd('''
        a: 1 #a
        s: '2 2' #s
        d: "3 3" #d
    '''),
    dd('''
        a: "1\\"2\\"3"
        s: '1"2"3'
    ''')
]

GET_TESTS = [{
    "input": dd('''
        a: 1
        s: 2
        d: 3
    '''),
    "path": ['s'],
    "get": [2]
},{
    "input": dd('''
        a:
          s:
            d: 1
    '''),
    "path": ['a', 's', 'd'],
    "get": [1]
},{
    "input": dd('''
        a:
          - s: {d: 1}
          - f: g
    '''),
    "path": ['a', 1, 's', 'd'],
    "get": [1]
},{
    "input": dd('''
        a:
          - s: {d: 1}
          - f: g
    '''),
    "path": ['a', 2, 'f'],
    "get": ['g']
}]

PUT_TESTS = [{
    "input": dd('''
        {}
    '''),
    "path": ['a'],
    "value": 1,
    "put": dd('''
        a: 1
    ''')
},{
    "input": dd('''
        a: 1
    '''),
    "path": ['s'],
    "value": 2,
    "put": dd('''
        a: 1
        s: 2
    ''')
},{
    "input": dd('''
        a: 1
        s: 2
    '''),
    "path": ['s'],
    "value": 3,
    "put": dd('''
        a: 1
        s: 3
    ''')
},{
    "input": dd('''
        a:
        - 1
    '''),
    "path": ['a', 0],
    "value": 2,
    "put": dd('''
        a:
        - 1
        - 2
    ''')
},{
    "input": dd('''
        a: 1
        s: [2] # ASD
        # DSA
    '''),
    "path": ['s', 0],
    "value": 3,
    "put": dd('''
        a: 1
        s: [2, 3] # ASD
        # DSA
    ''')
},{
    "input": dd('''
        a: 1
        s: [2] # ASD
        # DSA
    '''),
    "path": ['s', 1],
    "value": 3,
    "put": dd('''
        a: 1
        s: [3] # ASD
        # DSA
    ''')
},{
    "input": dd('''
        a: 1
        s: [2] # ASD
        # DSA
    '''),
    "path": ['x', 0],
    "value": 3,
    "put": dd('''
        a: 1
        s: [2] # ASD
        # DSA
        x:
        - 3
    ''')
},{
    "input": dd('''
        a: 1
    '''),
    "path": ['s'],
    "value": None,
    "put": dd('''
        a: 1
        s:
    ''')
}]

DROP_TESTS = [{
    "input": dd('''
        a: 1
        s: 2
        d: 3
    '''),
    "path": ['s'],
    "drop": dd('''
        a: 1
        d: 3
    ''')
},{
    "input": dd('''
        a:
        - s: 2
        - d: 3
    '''),
    "path": ['a', 1],
    "drop": dd('''
        a:
        - d: 3
    ''')
},{
    "input": dd('''
        a:
        - {s: 2, d: 3}
    '''),
    "path": ['a', 1, 's'],
    "drop": dd('''
        a:
        - {d: 3}
    ''')
}]

class TestYaml(unittest.TestCase):
    def test_ParseAndRender(self):
        for inp in PARSE_AND_RENDER_TESTS:
            yp = YamlParser(inp)
            yp.parse()
            self.assertEqual(yp.render(), inp)

    def test_Get(self):
        for d in GET_TESTS:
            yp = YamlParser(d['input'])
            yp.parse()
            self.assertEqual(yp.get(d['path']), d['get'])

    def test_Put(self):
        for d in PUT_TESTS:
            yp = YamlParser(d['input'])
            yp.parse()
            yp.put(d['path'], d['value'])
            self.assertEqual(yp.render(), d['put'])

    def test_Drop(self):
        for d in DROP_TESTS:
            yp = YamlParser(d['input'])
            yp.parse()
            yp.drop(d['path'])
            self.assertEqual(yp.render(), d['drop'])

if __name__ == '__main__':
    unittest.main()
