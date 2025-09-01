# frozen_string_literal: true

class ParserEngine
    class ParseFailure < StandardError; end

    def initialize(input)
        @input, @pos = input, 0
    end

    def zero_or_more(parser)
        matches = []
        loop { matches << backtrack { parser.call } }
    rescue ParseFailure
        matches
    end

    def one_of(*parsers)
        parsers.each do |parser|
            return backtrack { parser.call }
        rescue ParseFailure
            next
        end
        raise ParseFailure
    end

    def between(open, close, inner)
        backtrack { open.call; inner.call.tap { close.call } }
    end

    def peek(len = 1)
        ((s = input.byteslice(0, len)).length == len) ? s : (raise ParseFailure)
    end

    def take(len = 1)
        peek(len).tap { consume(len) }
    end

    def take_exact(pat)
        backtrack { ((s = take(pat.length)) == pat) ? s : (raise ParseFailure) }
    end

    def take_while(pred)
        s = +''
        loop { s << backtrack { pred.call(c = take) ? c : (raise ParseFailure) } }
        s
    rescue ParseFailure
        s
    end

    def quit
        raise ParseFailure
    end

    private

    def input
        @input.byteslice(@pos..(-1))
    end

    def consume(len = 1)
        @pos += len
    end

    def backtrack
        before = @pos
        yield
    rescue ParseFailure
        @pos = before
        raise
    end
end
