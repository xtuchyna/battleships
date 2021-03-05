# Additional types (classes) that you may want to define.

class Interface:

    def is_atom(self):
        return False

    def is_compound(self):
        return False

    def is_literal(self):
        return False

    def is_identifier(self):
        return False

    def is_number(self):
        return False

    def is_string(self):
        return False

    def is_bool(self):
        return False


class Atom(Interface):
    def __init__(self, value):
        self.value = value

    def is_atom(self):
        return True

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            other = other.value
        return self.value == other

    def __ne__(self, other):
        return not self.value == other


class Literal(Atom):
    def is_literal(self):
        return True


class Identifier(Atom):
    def is_identifier(self):
        return True

    def __repr__(self):
        return self.value


class Number(Literal):
    def is_number(self):
        return True

    def __add__(self, other):
        if isinstance(other, Number):
            other = other.value
        return Number(self.value + other)

    def __sub__(self, other):
        if isinstance(other, Number):
            other = other.value
        return Number(self.value - other)

    def __mul__(self, other):
        if isinstance(other, Number):
            other = other.value
        return Number(self.value * other)

    def __truediv__(self, other):
        if isinstance(other, Number):
            other = other.value
        return Number(self.value / other)

    def __radd__(self, other):
        if isinstance(other, Number):
            other = other.value
        return self + other

    def __rsub__(self, other):
        if isinstance(other, Number):
            other = other.value
        return Number(other - self.value)

    def __rmul__(self, other):
        if isinstance(other, Number):
            other = other.value
        return self * other

    def __rtruediv__(self, other):
        if isinstance(other, Number):
            other = other.value
        return Number(other / self.value)

    def __ge__(self, other):
        if isinstance(other, Number):
            other = other.value
        return self.value >= other

    def __lt__(self, other):
        if isinstance(other, Number):
            other = other.value
        return self.value < other

    def __gt__(self, other):
        return not self.value < other

    def __eq__(self, other):
        if isinstance(other, Number):
            other = other.value
        return self.value == other

    def __ne__(self, other):
        return not self.value == other

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __str__(self):
        return str(self.value)


class Bool(Literal):
    def is_bool(self):
        return True

    def __bool__(self):
        return self.value

    def __str__(self):
        return "#t" if self.value else "#f"


class String(Literal):
    def is_string(self):
        return True

    def __str__(self):
        return str(self.value)
