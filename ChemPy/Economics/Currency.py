class Currency:

    mode = 0
    unit = '$'

    def __init__(self, value, unit:str|None=None, mode:int|None=None):
        if isinstance(value,Currency):
            self.value=value.value
            self.unit=value.unit
            self.mode=value.mode
            return

        self.value = value
        if unit: self.unit = unit
        if mode: self.mode = mode

    def __repr__(self):
        return f'{self.unit}{self.value / 10 ** (3 * self.mode):0.2f} {"".join(self.mode * ["M"])}' \
            if self.value >= 0 else f'({self.unit}{self.value / 10 ** (3 * self.mode):0.2f}) {"".join(self.mode * ["M"])}'

    def __add__(self, other):
        if isinstance(other, Currency):
            if self.unit != other.unit:
                raise ValueError()
            return Currency(self.value + other.value)
        return Currency(self.value + float(other), self.unit, self.mode)

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        return Currency(self.value * other, self.unit, self.mode)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __float__(self):
        return float(self.value)

    @classmethod
    def Economize(cls,f):
        def new_f(x):
            return cls(f(x))

        return new_f
