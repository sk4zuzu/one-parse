# frozen_string_literal: true

require 'rspec'
require_relative '../ruby/rc'

PARSE_AND_RENDER_TESTS = [
    <<~INPUT,
        export A=1
        S=2
        D=3
    INPUT
    <<~INPUT,
        A='1'
        export S='2'
        D='3'
    INPUT
    <<~INPUT,
        A="1"
        S="2"
        export D="3"
    INPUT
    <<~INPUT,
        # A
            A=1

        export S='2' # S
        D="3"
         #D
    INPUT
    <<~INPUT,
        A=1 #A
            export S='2 2' #S
         D="3 3" #D
    INPUT
    <<~INPUT,
        A="1\\"2\\"3"
        S='1"2"3'
    INPUT
    '  A=S',
    '  A=S  '
]

RSpec.describe RcParser do
    it 'should parse then render identical content' do
        PARSE_AND_RENDER_TESTS.each do |input|
            (rc = RcParser.new input).parse
            expect(rc.render).to eq input
        end
    end
end

MATCH_AND_GET_TESTS = [{
    input: <<~INPUT,
        A=1
        S=2
        D=3
    INPUT
    path: 'S',
    match: ['S'],
    value: nil,
    get: ['2']
},{
    input: <<~INPUT,
        A=1
        S=2
        S=2
        D=3
    INPUT
    path: 'S',
    match: ['S[1]', 'S[2]'],
    value: nil,
    get: ['2', '2']
},{
    input: <<~INPUT,
        A=1
        S=2
        S=3
    INPUT
    path: '*',
    match: ['A', 'S[1]', 'S[2]'],
    value: nil,
    get: ['1', '2', '3']
},{
    input: <<~INPUT,
        A=1
        S=2
        S=3
    INPUT
    path: 'A[0]',
    match: [],
    value: nil,
    get: []
},{
    input: <<~INPUT,
        A=1
        S=2
        S=3
        D=4
        D=5
    INPUT
    path: 'S[0]',
    match: ['S[1]', 'S[2]'],
    value: nil,
    get: ['2', '3']
},{
    input: <<~INPUT,
        A=1
        S=2
        S=3
        D=4
        D=5
    INPUT
    path: '*[0]',
    match: ['S[1]', 'S[2]', 'D[1]', 'D[2]'],
    value: nil,
    get: ['2', '3', '4', '5']
},{
    input: <<~INPUT,
        A=1
        S=2
        S=3
        D=4
        D=5
    INPUT
    path: '*[0]',
    match: ['S[2]'],
    value: '3',
    get: ['2', '3', '4', '5']
}]

RSpec.describe RcParser do
    it 'should match and extract values' do
        MATCH_AND_GET_TESTS.each do |d|
            (rc = RcParser.new d[:input]).parse
            expect(rc.match d[:path], d[:value]).to eq d[:match]
            expect(rc.get   d[:path]).to            eq d[:get]
        end
    end
end

PUT_TESTS = [{
    input: <<~INPUT,
    INPUT
    path: 'A',
    value: '1',
    put: <<~OUTPUT,
        A=1
    OUTPUT
},{
    input: <<~INPUT,
        A=1
    INPUT
    path: 'S',
    value: '2',
    put: <<~OUTPUT,
        A=1
        S=2
    OUTPUT
},{
    input: <<~INPUT,
        A=1
        S=2
    INPUT
    path: 'S',
    value: '3',
    put: <<~OUTPUT,
        A=1
        S=3
    OUTPUT
},{
    input: <<~INPUT,
        A=1
    INPUT
    path: 'A[0]',
    value: '2',
    put: <<~OUTPUT,
        A=1
        A=2
    OUTPUT
},{
    input: <<~INPUT,
        A=1
        S=2
    INPUT
    path: 'S[0]',
    value: '3',
    put: <<~OUTPUT,
        A=1
        S=2
        S=3
    OUTPUT
},{
    input: <<~INPUT,
        A=1
        S=2 # ASD
        # DSA
    INPUT
    path: 'S[0]',
    value: '3',
    put: <<~OUTPUT,
        A=1
        S=2 # ASD
        # DSA
        S=3
    OUTPUT
},{
    input: <<~INPUT,
        A=1
    INPUT
    path: 'S',
    value: '',
    put: <<~OUTPUT,
        A=1
        S=
    OUTPUT
}]

RSpec.describe RcParser do
    it 'should put values' do
        PUT_TESTS.each do |d|
            (rc = RcParser.new d[:input]).parse
            rc.put d[:path], d[:value]
            expect(rc.render).to eq d[:put]
        end
    end
end

DROP_TESTS = [{
    input: <<~INPUT,
        A=1
        S=2
        D=3
    INPUT
    path: 'S',
    value: nil,
    drop: <<~OUTPUT,
        A=1
        D=3
    OUTPUT
},{
    input: <<~INPUT,
        A=1
        S=2
        D=3
        export S=4
    INPUT
    path: 'S',
    value: nil,
    drop: <<~OUTPUT,
        A=1
        D=3
    OUTPUT
},{
    input: <<~INPUT,
        A=1
        S=2
        D=3
        export S=4
    INPUT
    path: 'S[1]',
    value: nil,
    drop: <<~OUTPUT,
        A=1
        D=3
        export S=4
    OUTPUT
},{
    input: <<~INPUT,
        A=1
        S=2
        D=3
        export S=4
    INPUT
    path: 'S[2]',
    value: nil,
    drop: <<~OUTPUT,
        A=1
        S=2
        D=3
    OUTPUT
}]

RSpec.describe RcParser do
    it 'should drop values' do
        DROP_TESTS.each do |d|
            (rc = RcParser.new d[:input]).parse
            rc.drop d[:path], d[:value]
            expect(rc.render).to eq d[:drop]
        end
    end
end
