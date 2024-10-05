# stplib: a library for manipulating stp (step) files.
# Copyright (C) 2024  CToID <funk443@yahoo.com.tw>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from lark import Lark, Transformer


# ---- FIX ME! ----
# URI, RESOURCE, ANCHOR_NAME, and SIGNATURE_CONTENT
# not implemented.
grammar = r"""
%import common.WS
%ignore WS

SPACE: " "
DIGIT: "0" .. "9"
UPPER: "A" .. "Z" | "_"
LOWER: "a" .. "z"
SPECIAL: "!"
    | "*"
    | "$"
    | "%"
    | "&"
    | "."
    | "#"
    | "+"
    | ","
    | "-"
    | "("
    | ")"
    | "?"
    | "/"
    | ":"
    | ";"
    | "<"
    | "="
    | ">"
    | "@"
    | "["
    | "]"
    | "{"
    | "|"
    | "}"
    | "^"
    | "`"
    | "~"
    | "\""
REVERSE_SOLIDUS: "\\"
APOSTROPHE: "'"
LATIN_CODE_POINT: SPACE
    | DIGIT
    | LOWER
    | UPPER
    | SPECIAL
    | REVERSE_SOLIDUS
    | APOSTROPHE
HIGH_CODEPOINT: /[u"\u0080-\u10ffff"]/

INNER_STANDARD_KEYWORD: UPPER (UPPER | DIGIT)*
?keyword: user_difined_keyword | standard_keyword
user_difined_keyword: "!" INNER_STANDARD_KEYWORD
standard_keyword: INNER_STANDARD_KEYWORD

SIGN: "+" | "-"
INNER_INTEGER: SIGN? DIGIT+
integer: INNER_INTEGER
INNER_REAL: SIGN? DIGIT+ "." DIGIT* ("E" SIGN? DIGIT+)?
real: INNER_REAL

INNER_STRING: (SPECIAL
     | DIGIT
     | SPACE
     | LOWER
     | UPPER
     | APOSTROPHE APOSTROPHE
     | REVERSE_SOLIDUS REVERSE_SOLIDUS)+
string: "'" INNER_STRING? "'"

INNER_INSTANCE_NAME: DIGIT+
entity_instance_name: "#" INNER_INSTANCE_NAME
value_instance_name: "@" INNER_INSTANCE_NAME

INNER_CONSTANT_NAME:  UPPER (UPPER | DIGIT)*
constant_entity_name: "#" INNER_CONSTANT_NAME
constant_value_name: "@" INNER_CONSTANT_NAME

?lhs_occurance_name: entity_instance_name
    | value_instance_name
?rhs_occurance_name: entity_instance_name
    | value_instance_name
    | constant_entity_name
    | constant_value_name

INNER_TAG_NAME: (UPPER | LOWER) (UPPER | LOWER | DIGIT)*
tag_name: INNER_TAG_NAME

INNER_ENUMERATION: UPPER (UPPER | DIGIT)*
enumeration: "." INNER_ENUMERATION "."

universal_fragment_identifier: "#" (LOWER | UPPER | DIGIT | SPECIAL)+
universal_resource_identifier: "FIXME!"
resource: "<" universal_resource_identifier ">"

signature_content: "FIXME!!"

HEX: "0" .. "9" | "A" .. "F"
binary: "\"" ("0" .. "3") HEX* "\""

exchange_file: "ISO-10303-21;" \
    header_section \
    anchor_section? \
    reference_section? \
    data_section* \
    "END-ISO-10303-21;" \
    signature_section*

header_section: "HEADER;" \
    header_entity header_entity header_entity \
    header_entity_list? \
    "ENDSEC;"
header_entity_list: header_entity+
header_entity: keyword "(" parameter_list? ")" ";"

parameter_list: parameter ("," parameter)*
?parameter: typed_parameter
    | untyped_parameter
    | omitted_parameter
typed_parameter: keyword "(" parameter ")"
?untyped_parameter: "$"
    | integer
    | real
    | string
    | rhs_occurance_name
    | enumeration
    | binary
    | list
?omitted_parameter: "*"

list: "(" (parameter ("," parameter)*)? ")"

anchor_section: "ANCHOR;" anchor_list "ENDSEC;"
anchor_list: anchor*
anchor: anchor_name "=" anchor_item anchor_tag* ";"
anchor_name: "<" universal_fragment_identifier ">"
anchor_item: "$"
    | integer
    | real
    | string
    | enumeration
    | binary
    | rhs_occurance_name
    | resource
    | anchor_item_list
anchor_item_list: "(" (anchor_item ("," anchor_item)*)? ")"
anchor_tag: "{" tag_name ":" anchor_item "}"

reference_section: "REFERENCE;" reference_list "ENDSEC;"
reference_list: reference*
reference: lhs_occurance_name "=" resource ";"

data_section: "DATA" ("(" parameter_list ")")? ";" \
    entity_instance_list \
    "ENDSEC;"
entity_instance_list: entity_instance*
?entity_instance: simple_entity_instance
    | complex_entity_instance
simple_entity_instance: entity_instance_name "=" simple_record ";"
complex_entity_instance: entity_instance_name "=" subsuper_record ";"
simple_record: keyword "(" parameter_list? ")"
?subsuper_record: "(" simple_record_list ")"
simple_record_list: simple_record+

signature_section: "SIGNATURE" signature_content "ENDSEC;"
"""



class SimpleObject():
    def __init__(self, value):
        self.value = value


class StandardKeyword(SimpleObject):
    def __repr__(self):
        return self.value


class CustomKeyword(SimpleObject):
    def __repr__(self):
        return f"!{self.value}"


class Enumeration(SimpleObject):
    def __repr__(self):
        return f".{self.value}."


class SimpleRecord():
    def __init__(self, keyword, args):
        self.keyword = keyword
        self.args = args

    def __repr__(self):
        return f"{self.keyword}({self.args})"


class HeaderEntity(SimpleRecord):
    pass


class TypedParameter(SimpleRecord):
    pass



class TreeToStp(Transformer):
    def exchange_file(self, sections):
        stp = {}
        for k, v in sections:
            stp[k] = v

        return stp

    def header_section(self, items):
        return ("header", items)

    def data_section(self, items):
        # There could have multiple data sections
        assert len(items) == 1
        return ("data", items[-1])

    def header_entity(self, items):
        return HeaderEntity(
            keyword = items[0],
            args = items[1] if len(items) > 1 else [])

    def simple_record(self, items):
        return SimpleRecord(
            keyword = items[0],
            args = items[1] if len(items) > 1 else [])

    def standard_keyword(self, item):
        return StandardKeyword(item[0])

    def user_difined_keyword(self, item):
        return CustomKeyword(item[0])

    def real(self, item):
        return float(item[0])

    def integer(self, item):
        return int(item[0])

    def string(self, item):
        if not item:
            return ""

        return str(item[0])

    def enumeration(self, item):
        return Enumeration(item[0])

    def list(self, items):
        return items

    def parameter_list(self, items):
        return items

    def entity_instance_list(self, items):
        entities = {}
        for k, v in items:
            entities[k] = v

        return entities

    def entity_instance_name(self, item):
        return f"#{item[0]}"

    def value_instance_name(self, item):
        return f"@{item[0]}"

    def simple_entity_instance(self, items):
        return tuple(items)

    def simple_record_list(self, items):
        return items

    def complex_entity_instance(self, items):
        return tuple(items)

    def untyped_parameter(self, item):
        assert not item
        return "$"

    def omitted_parameter(self, item):
        assert not item
        return "*"

    def typed_parameter(self, item):
        assert len(item) > 1
        return TypedParameter(
            keyword = item[0],
            args = item[1])



l = Lark(grammar, start = "exchange_file")


filename = "./test.stp"
with open(filename, "r", encoding = "utf-8") as f:
    stp_content =  l.parse(f.read())

stp = TreeToStp().transform(stp_content)
