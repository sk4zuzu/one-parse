# frozen_string_literal: true

require_relative 'base'

class OneParser < ParserBase
    class Vector < Sequence; end

    PARSER_PROC = proc {
        quoted = proc {
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
            peek[/[^\]\[\"\,\#[:space:]]/] \
                ? (take_while proc { |c| c[/[^\]\[\"\,\#[:space:]]/] })
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
            Pair[ blank.call,
                  attribute.call,
                  blank.call + (take_exact %[\=]) + blank.call,
                  (one_of quoted,
                          unquoted),
                  (one_of comment,
                          blank_eol,
                          blank) ]
        }

        blank_comma = proc { blank.call.tap { take_exact %[\,] } }

        item = proc {
            Pair[ blank.call,
                  attribute.call,
                  blank.call + (take_exact %[\=]) + blank.call,
                  (one_of quoted,
                          unquoted),
                  (one_of proc { Comment[ blank_comma.call + comment.call ] },
                          proc { blank_comma.call + blank_eol.call },
                          blank_comma,
                          comment,
                          blank_eol,
                          blank) ]
        }

        vector = proc {
            Vector[ blank.call,
                    attribute.call,
                    blank.call + (take_exact %[\=]) + blank.call,
                    (between proc { take_exact %[\[] },
                             proc { take_exact %[\]] },
                             proc { Sequence[ *(zero_or_more proc { one_of item,
                                                                           comment,
                                                                           blank_eol }) ] }),
                    (one_of comment,
                            blank_eol,
                            blank) ]
        }

        Sequence[ *(zero_or_more proc { one_of pair,
                                               vector,
                                               comment,
                                               blank_eol }) ]
    }

    def initialize(input)
        super(input, PARSER_PROC)
    end

    def render(node = @parsed)
        node.each_with_object(+'') do |vv, acc|
            case
            when vv.is_a?(String)
                acc << vv
            when vv.is_a?(Pair)
                acc << vv.join
            when vv.is_a?(Vector)
                acc << vv[0..2].join
                acc << %[\[]
                count = vv[3].count { |v| v.is_a?(Pair) }
                vv[3].each do |v|
                    case
                    when v.is_a?(String)
                        acc << v
                    when v.is_a?(Pair)
                        acc << v[0..3].join
                        acc << %[\,] if (count -= 1) > 0
                        acc << v[4]
                    else
                        raise InvalidTree
                    end
                end
                acc << %[\]]
                acc << vv[4]
            else
                raise InvalidTree
            end
        end
    end

    def put(path, value)
        atrb, atrb_i, item, item_i = ypath path, wildcards: false
        s = searchable
        case
        # add a new pair directly at the root level
        when (s[atrb].nil? || (!atrb_i.nil? && atrb_i == 0)) && item.nil?
            @parsed << Pair[
                %[], atrb, %[ \= ], value.to_s, %[\n]
            ]

        # add a new vector with a single pair directly at the root level
        when (s[atrb].nil? || (!atrb_i.nil? && atrb_i == 0)) && !item.nil?
            @parsed << Vector[
                %[], atrb, %[ \= ], Sequence[
                    %[\n], Pair[
                        %[ ], item, %[ \= ], value.to_s, %[ ]
                    ]
                ], %[\n]
            ]

        # require paths to be unequivocal
        when atrb_i.nil? && s[atrb].length > 1
            raise AmbiguousMatch

        # fail when nothing found
        when (s = s.dig(atrb, atrb_i.nil? ? 0 : (atrb_i - 1))).nil?
            raise EmptyMatch

        # when second pattern is provided then first one must not resolve into a pair
        # when second pattern is not provided then first one must resolve into a pair
        when item.nil? ^ s.is_a?(Pair)
            raise InvalidPath

        # update the value (root level)
        when item.nil?
            s[3] = value.to_s

        # add a new pair to an existing vector
        when s[item].nil? || (!item_i.nil? && item_i == 0)
            parent = s.dig(s.keys[0], 0).getm(:@_parent_) # get parent from a neighbor pair
            indent = infer_vector_indent parent
            # apply suffix correction to the former last pair
            indent[:prev_pair][4] = indent[:prev_suffix]
            # append new correctly indented pair
            parent << Pair[
                indent[:next_prefix], item, %[ \= ], value.to_s, indent[:next_suffix]
            ]

        # require paths to be unequivocal
        when item_i.nil? && s[item].length > 1
            raise AmbiguousMatch

        # fail when nothing found
        when (s = s.dig(item, item_i.nil? ? 0 : (item_i - 1))).nil?
            raise EmptyMatch

        # second pattern must resolve into a pair
        when !s.is_a?(Pair)
            raise InvalidPath

        # update the value (vector level)
        else
            s[3] = value.to_s
        end
    end

    def drop(path, value = nil)
        atrb, atrb_i, item, item_i = ypath path, wildcards: true
        (recurse = proc { |node| # NOTE: never use default values here!
            case
            when node.is_a?(Pair) && (value.nil? || node[3] == value.to_s)
                parent = node.getm(:@_parent_)
                # delete first found (should be only one)
                parent.delete_at(parent.index { |x| x.object_id == node.object_id } || parent.length)
            when node.is_a?(Sequence)
                node.each { |v| recurse.call v }
            when node.is_a?(Lookup)
                node.each { |_, v| recurse.call v }
            end
        }).call (filtered patterns: [atrb, item], indices: [atrb_i, item_i])
        # remove empty vectors
        @parsed.each do |node|
            case
            when node.is_a?(Vector) && (node[3].reject { |v| !v.is_a?(Pair) }).empty?
                # delete first found (should be only one)
                @parsed.delete_at(@parsed.index { |x| x.object_id == node.object_id } || @parsed.length)
            end
        end
    end

    private

    def ypath(path, wildcards: true)
        path = path.join(%[\/]) if path.is_a?(Array)
        wild = wildcards ? %[\*] : %[]
        regx = %r{ ^
                   ( [[:alnum:]_#{wild}]+ )
                   (?:
                       \[ ( [[:digit:]]* ) \]
                   )?
                   (?:
                       /
                       ( [[:alnum:]_#{wild}]+ )
                       (?:
                           \[ ( [[:digit:]]* ) \]
                       )?
                   )?
                   $ }x
        raise InvalidPath if (m = regx.match(path)).nil?

        atrb   = m[1]
        atrb_i = m[2].to_s.empty? ? nil : m[2].to_i
        item   = m[3]
        item_i = m[4].to_s.empty? ? nil : m[4].to_i
        raise InvalidPath if atrb.nil? \
                          || (item.nil? && !item_i.nil?) \
                          || (!atrb_i.nil? && atrb_i.to_i < 0) \
                          || (!item_i.nil? && item_i.to_i < 0)

        [atrb, atrb_i, item, item_i]
    end

    def searchable(node = @parsed)
        ((recurse = proc { |node| # NOTE: never use default values here!
            node.each_with_object(Lookup[]) do |v, acc|
                # @_parent_ values are used later during put and drop operations
                case
                when v.is_a?(Pair)
                    (acc[v[1]] ||= Sequence[]) << v
                    v.setm(:@_parent_, node)
                when v.is_a?(Vector)
                    (acc[v[1]] ||= Sequence[]) << (recurse.call v[3])
                    v.setm(:@_parent_, node)
                end
            end
        }).call node).then do |node|
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

    def infer_vector_indent(parent)
        parent.each_with_object({
            :has_eol => false,
            :prev_pair => nil,
            :next_prefix => %[],
            :prev_suffix => %[],
            :next_suffix => %[]
        }) do |node, acc|
            case
            when node.is_a?(String)
                acc[:has_eol] = true if node.include?(%[\n])
            when node.is_a?(Pair)
                acc[:has_eol] = true if node[4].include?(%[\n])
                acc[:prev_pair] = node
            end
        end.then do |acc|
            acc[:next_prefix] = acc[:prev_pair][0].dup
            if (s = acc[:prev_pair][4]).is_a?(Comment)
                acc[:prev_suffix] = s.dup
                acc[:next_suffix] = %[ ]
            else
                acc[:prev_suffix] = acc[:has_eol] ? %[\n] : %[]
                acc[:next_suffix] = s.dup
            end
            acc
        end
    end
end
