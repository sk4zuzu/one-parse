# frozen_string_literal: true

require_relative 'engine'

class ParserBase < ParserEngine
    class InvalidPath    < StandardError; end
    class InvalidTree    < StandardError; end
    class AmbiguousMatch < StandardError; end
    class EmptyMatch     < StandardError; end

    module Meta
        def setm(k, v); self.instance_variable_set(k, v); self; end
        def getm(k); self.instance_variable_get(k); end
    end

    class Lookup   < Hash; include Meta; end
    class Sequence < Array; include Meta; end
    class Pair     < Sequence; end

    class Comment < String
        include Meta
        def self.[](s); s.include?(%[\#]) ? Comment.new(s) : String.new(s); end
    end

    def initialize(input, parser_proc)
        super(input)
        @parser_proc = parser_proc
    end

    def parse
        (@parsed = instance_eval &@parser_proc).tap do
            next unless input.length > 0
            line = @input[0...@pos].count(%[\n]) + 1
            text = @input[@pos..(@pos + 15)].split(%[\n], 2)[0]
            raise ParseFailure, "line #{line}, at `#{text}..'"
        end
    end

    def render(node = @parsed)
        raise NotImplementedError
    end

    def match(path, value = nil)
        atrb, atrb_i, item, item_i = ypath path, wildcards: true
        (recurse = proc { |node, prefix, acc| # NOTE: never use default values here!
            case
            when node.is_a?(Pair) && (value.nil? || node[3] == value.to_s)
                index = (i = node.getm(:@_index_)).nil? ? '' : "[#{i}]"
                acc << (prefix + index)
            when node.is_a?(Sequence)
                node.each { |v| recurse.call v, prefix, acc }
            when node.is_a?(Lookup)
                unless prefix.empty?
                    index = (i = node.getm(:@_index_)).nil? ? '' : "[#{i}]"
                    prefix += (index + %[\/])
                end
                node.each { |k, v| recurse.call v, prefix + k, acc }
            end
        }).call (filtered patterns: [atrb, item], indices: [atrb_i, item_i]), '', (found = [])
        found
    end

    def get(path)
        atrb, atrb_i, item, item_i = ypath path, wildcards: true
        (recurse = proc { |node, acc| # NOTE: never use default values here!
            case
            when node.is_a?(Pair)
                acc << node[3]
            when node.is_a?(Sequence)
                node.each { |v| recurse.call v, acc }
            when node.is_a?(Lookup)
                node.each { |_, v| recurse.call v, acc }
            end
        }).call (filtered patterns: [atrb, item], indices: [atrb_i, item_i]), (found = [])
        found
    end

    def put(path, value)
        raise NotImplementedError
    end

    def drop(path, value = nil)
        raise NotImplementedError
    end

    private

    def ypath(path, wildcards: true)
        raise NotImplementedError
    end

    def searchable(node = @parsed)
        raise NotImplementedError
    end

    def filtered(node = @parsed, patterns: [], indices: [])
        (recurse = proc { |node, patterns, indices| # NOTE: never use default values here!
            case
            when node.is_a?(Pair)
                node if patterns.empty?
            when node.is_a?(Lookup)
                case
                when !(pat = patterns.shift).nil?
                    node.each_with_object({}) do |(k, vv), acc|
                        if File.fnmatch?(pat, k)
                            v = recurse.call vv, patterns.dup, indices.dup
                            acc[k] = v unless v.nil?
                        end
                    end.then do |acc|
                        # because the hash is recreated, the value of @_index_ must be copied over
                        Lookup[**acc].setm(:@_index_, node.getm(:@_index_)) unless acc.empty?
                    end
                end
            when node.is_a?(Sequence)
                case
                # [0] is supposed to match repeated pairs exclusively
                when (index = indices.shift).nil? || (index.zero? && node.length > 1)
                    node.each_with_object([]) do |vv, acc|
                        v = recurse.call vv, patterns.dup, indices.dup
                        acc << v unless v.nil?
                    end.compact.then do |acc|
                        Sequence[*acc] unless acc.empty?
                    end
                when !index.nil? && !index.zero? && node.length > 1 && !(vv = node[index - 1]).nil?
                    v = recurse.call vv, patterns.dup, indices.dup
                    Sequence[v] unless v.nil?
                end
            end
        }).call (searchable node), patterns.dup.compact, indices.dup
    end
end
