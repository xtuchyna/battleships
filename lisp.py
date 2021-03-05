# Implement ‹parse› here. You can define helper classes either here
# or in ‹classes.py› (the latter will not be directly imported by
# the tests).
from classes import Bool, Number, Identifier, String, Interface

ID_SYMBOL = {'!', '$', '%', '&', '*', '/', ':', '<', '=', '>', '?', '_', '~'}
ID_SPECIAL = {'+', '-', '.', '@', '#'}
DIGIT = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
SIGN = {'+', '-'}


class NotParsable(Exception):
    pass


class Compound(Interface):
    def __init__(self, compounds):
        self.compounds = compounds

    def is_compound(self):
        return True

    def __iter__(self):
        return iter(self.compounds)

    def __len__(self):
        return len(self.compounds)

    def __getitem__(self, key):
        return self.compounds[key]

    def __eq__(self, other):
        if isinstance(other, Compound):
            return self.compounds == other.compounds

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return "(" + " ".join([str(e) for e in self.compounds]) + ")"


class Parser:
    def __init__(self, expr, position, is_nested=False):
        self.expr = expr
        self.position = position
        self.inner_counter = 0
        self.expected_closure = ""
        self.expressions = []
        self.is_nested = is_nested

    @staticmethod
    def is_ending_parentheses(char):
        return char == ')' or char == ']'

    @staticmethod
    def is_atom_ending(char):
        return char.isspace() or Parser.is_ending_parentheses(char)

    def process_bool(self):
        if self.position + 1 >= len(self.expr):
            return False

        if self.expr[self.position] != "#":
            return False

        bool_indicator = self.expr[self.position + 1]
        if bool_indicator != 'f' and bool_indicator != 't':
            return False

        # after #t | #f there must be either space or end
        if not self.position + 2 >= len(self.expr):
            ending = self.expr[self.position + 2]
            if not ending.isspace() and not Parser.is_ending_parentheses(ending):
                return False

        # all checks passed, all clear
        self.expressions.append(Bool(True) if bool_indicator == 't' else Bool(False))
        self.position += 2
        return True

    def process_number(self):
        position = self.position
        char = self.expr[position]
        whole_number = ""
        if char not in SIGN and not char.isnumeric():
            return False

        if char in SIGN:
            # after sign there has to be some numeric
            if not (position + 1 < len(self.expr) and self.expr[position + 1].isnumeric()):
                return False
            whole_number += char
            position += 1

        while True:
            if position == len(self.expr):
                break

            char = self.expr[position]

            if self.is_atom_ending(char):
                break

            if not (char == "." or char.isnumeric()):  # single dot check later
                return False

            whole_number += char
            position += 1

        floating = '.' in whole_number
        if floating:
            try:
                float(whole_number)
            except ValueError:
                return False
            split = whole_number.split('.')
            if (len(split) != 2
                    or not split[0]
                    or not split[1]):
                return False

        number = float(whole_number) if floating else int(whole_number)
        self.expressions.append(Number(number))
        self.position = position
        return True

    def process_string(self):
        position = self.position
        char = self.expr[position]
        if char != "\"":
            return False

        whole_string = "\""

        while True:
            if position + 1 == len(self.expr):
                # at least two chars
                if position == self.position:
                    return False
                # always ends with " if singleton
                if self.expr[position] != "\"":
                    return False

            position += 1
            char = self.expr[position]

            # end of string
            if char == "\"":
                whole_string += "\""
                position += 1
                break

            # special char sequences \" and \\
            elif char == "\\":

                if position + 1 >= len(self.expr):
                    return False

                second_char = self.expr[position + 1]
                if second_char == "\\" or second_char == "\"":
                    # special seq cannot
                    if not position + 2 <= len(self.expr):
                        raise NotParsable
                    if second_char == "\"":
                        if not position + 2 != len(self.expr):
                            raise NotParsable
                    whole_string += self.expr[position:position + 2]
                    position += 1
                else:
                    return False  # standalone '\' not permitted

            else:
                whole_string += char

            # anything else not valid
            # else:
            #     return False

        # if not whole_string:
        #     return False

        self.expressions.append(String(whole_string))
        self.position = position
        return True

    def process_literal(self):
        return (self.process_bool()
                or self.process_number()
                or self.process_string())

    @staticmethod
    def check_id_init(char):
        return char.isalpha() or char in ID_SYMBOL

    @staticmethod
    def check_id_subseq(char):
        return (Parser.check_id_init(char)
                or char in DIGIT
                or char in ID_SPECIAL)

    def is_identifier_singleton(self):
        pass

    def process_identifier(self):
        position = self.position
        char = self.expr[position]

        # singleton sign check
        if char in SIGN:

            if position + 1 < len(self.expr):
                if not Parser.is_atom_ending(self.expr[position+1]):
                    return False
            elif not position + 1 == len(self.expr):
                return False

            self.position += 1
            self.expressions.append(Identifier(char))
            return True

        # id_init, {id_subseq}
        id_init = False
        while True:
            if position == len(self.expr):
                break
            char = self.expr[position]

            if not id_init:
                if not Parser.check_id_init(char):
                    return False
                id_init = True

            if Parser.is_atom_ending(char):
                break

            if not Parser.check_id_subseq(char):
                return False

            position += 1

        identifier = self.expr[self.position:position]  # include last char
        self.position = position
        self.expressions.append(Identifier(identifier))
        return True

    def process_atom(self):
        return self.process_literal() or self.process_identifier()

    def nested(self):
        nested = Parser(expr=self.expr, position=self.position, is_nested=True)
        self.expressions.append(nested.parse())
        self.position = nested.position

    def parse(self):
        atom_processed = False
        from_nested = False
        while True:
            try:
                char = self.expr[self.position]
            except IndexError:
                return None

            # new compound found
            if char == "(" or char == "[":
                if not self.expected_closure:  # base compound
                    self.expected_closure = ")" if char == "(" else "]"
                else:
                    self.nested()    # nested compound
                    from_nested = True

            # current compound parser is done and can return
            elif Parser.is_ending_parentheses(char):
                if not char == self.expected_closure:
                    raise NotParsable
                if self.is_nested:
                    self.position += 1
                else:
                    if not self.position + 1 == len(self.expr):
                        raise NotParsable
                break

            # atom found
            elif not char.isspace():
                # singleton can be only one
                if not self.expected_closure and self.expressions:
                    raise NotParsable

                atom_processed = self.process_atom()
                if not atom_processed:
                    raise NotParsable

                # singleton has to be at the end
                if not self.expected_closure:
                    if not self.position == len(self.expr):
                        raise NotParsable

            elif char.isspace():
                pass

            # character not known
            else:
                raise NotParsable

            # in case of singleton
            if self.position == len(self.expr):
                if self.expected_closure:
                    raise NotParsable
                break

            if self.position + 1 == len(self.expr):
                if self.expected_closure:
                    if not self.expr[self.position] == self.expected_closure:
                        raise NotParsable
                self.position += 1
                break

            # after atom_processed, position points to already new char
            if atom_processed:
                atom_processed = False

            # same for the  from nested
            elif from_nested:
                from_nested = False
                if (len(self.expressions) > 1
                        and self.expr[self.position] != ')'
                        and self.expr[self.position] != ']'):
                    if not self.expr[self.position].isspace():
                        raise NotParsable
            else:
                self.position += 1

        # empty expression of any kind not permitted
        if not self.expressions:
            raise NotParsable

        # singleton
        if not self.expected_closure:
            if not len(self.expressions) == 1:  # should be one and only element then
                raise NotParsable
            return self.expressions[0]  # return value is the element itself

        # compound
        return Compound(self.expressions)


def parse(expr):
    if not expr:
        return None
    parser = Parser(expr.strip(), 0)
    try:
        x = parser.parse()
    except NotParsable:
        return None
    return x
