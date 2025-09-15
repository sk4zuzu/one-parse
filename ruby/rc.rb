# frozen_string_literal: true

require_relative 'base'

class RcParser < ParserBase
    PARSER_PROC = proc {
        single_quoted = proc {
            between proc { take_exact %[\'] },
                    proc { take_exact %[\'] }, proc {
                %[\'] + (take_while proc { |c| c != %[\'] }) + %[\']
            }
        }

        double_quoted = proc {
            between proc { take_exact %[\"] },
                    proc { take_exact %[\"] }, proc {
                escaped = false
                %[\"] + (take_while proc { |c|
                    (c == %[\\] || (c == %[\"] && escaped)) \
                        ? (escaped = !escaped; true)
                        : (c != %[\"])
                }) + %[\"]
            }
        }

        unquoted = proc {
            peek[/[^\#[:space:]]/] \
                ? (take_while proc { |c| c[/[^\#[:space:]]/] })
                : quit
        }

        attribute = proc { take_while proc { |c| c[/[[:alnum:]_]/] } }

        blank = proc { take_while proc { |c| c[/[[:blank:]]/] } }

        eol = proc { take_exact %[\n] }

        blank_eol = proc { blank.call + eol.call }

        comment = proc {
            Comment[ (blank.call + (take_exact %[\#]) \
                                 + (take_while proc { |c| c != %[\n] }) \
                                 + eol.call) ]
        }

        pair = proc {
            Pair[ (one_of proc { blank.call + (take_exact %[export]) + blank.call },
                          blank),
                  attribute.call,
                  (take_exact %[\=]),
                  (one_of single_quoted,
                          double_quoted,
                          unquoted,
                          blank),
                  (one_of comment,
                          blank_eol,
                          blank) ]
        }

        Sequence[ *(zero_or_more proc { one_of pair,
                                               comment,
                                               blank_eol }) ]
    }

    def initialize(input)
        super(input, PARSER_PROC)
    end

    def render(node = @parsed)
        node.each_with_object(+'') do |v, acc|
            case
            when v.is_a?(String)
                acc << v
            when v.is_a?(Pair)
                acc << v.join
            else
                raise InvalidTree
            end
        end
    end

    def put(path, value)
        atrb, atrb_i = ypath path, wildcards: false
        s = searchable
        case
        # add a new pair directly at the root level
        when s[atrb].nil? || (!atrb_i.nil? && atrb_i == 0)
            @parsed << Pair[
                %[], atrb, %[\=], value.to_s, %[\n]
            ]

        # require paths to be unequivocal
        when atrb_i.nil? && s[atrb].length > 1
            raise AmbiguousMatch

        # fail when nothing found
        when (s = s.dig(atrb, atrb_i.nil? ? 0 : (atrb_i - 1))).nil?
            raise EmptyMatch

        # the pattern must resolve into a pair
        when !s.is_a?(Pair)
            raise InvalidPath

        # update the value (root level)
        else
            s[3] = value.to_s
        end
    end

    def drop(path, value = nil)
        atrb, atrb_i = ypath path, wildcards: true
        (recurse = proc { |node| # NOTE: never use default values here!
            case
            when node.is_a?(Pair) && (value.nil? || node[3] == value.to_s)
                # delete first found (should be only one)
                @parsed.delete_at(@parsed.index { |x| x.object_id == node.object_id } || @parsed.length)
            when node.is_a?(Sequence)
                node.each { |v| recurse.call v }
            when node.is_a?(Lookup)
                node.each { |_, v| recurse.call v }
            end
        }).call (filtered patterns: [atrb, nil], indices: [atrb_i, nil])
    end

    private

    def ypath(path, wildcards: true)
        wild = wildcards ? %[\*] : %[]
        regx = %r{ ^
                   ( [[:alnum:]_#{wild}]+ )
                   (?:
                       \[ ( [[:digit:]]* ) \]
                   )?
                   $ }x
        raise InvalidPath if (m = regx.match(path)).nil?

        atrb   = m[1]
        atrb_i = m[2].to_s.empty? ? nil : m[2].to_i
        raise InvalidPath if atrb.nil? \
                          || (!atrb_i.nil? && atrb_i.to_i < 0)

        [atrb, atrb_i, nil, nil]
    end

    def searchable(node = @parsed)
        node.each_with_object(Lookup[]) do |v, acc|
            case
            when v.is_a?(Pair)
                (acc[v[1]] ||= Sequence[]) << v
            end
        end.then do |node|
            # at this point it's possible to easily compute and attach index metadata
            (recurse = proc { |node, index| # NOTE: never use default values here!
                case
                when node.is_a?(Pair)
                    node.setm(:@_index_, index)
                when node.is_a?(Sequence)
                    # when the node has less than 2 items the value of @_index_ must be unset
                    node.each_with_index { |v, i| recurse.call v, ((node.length > 1) ? (i + 1) : nil) }
                when node.is_a?(Lookup)
                    node.setm(:@_index_, index)
                    node.each { |_, v| recurse.call v, nil }
                end
            }).call node, nil
            node
        end
    end
end
