import numpy as np


class Currency:

    mode = None
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
        elif not self.mode: self.mode = int(np.log(np.abs(self.value))//np.log(1e3)) if self.value != 0 else 0

    def __repr__(self):
        return f'{self.unit}{self.value / 10 ** (3 * self.mode):0.2f} {"".join(self.mode * ["M"])}' \
            if self.value >= 0 else f'({self.unit}{self.value / 10 ** (3 * self.mode):0.2f}) {"".join(self.mode * ["M"])}'

    def __add__(self, other):
        if isinstance(other, Currency):
            if self.unit != other.unit:
                raise ValueError()
            return Currency(self.value + other.value)
        return Currency(self.value + float(other), self.unit)

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        return Currency(self.value * other, self.unit)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __sub__(self,other):
        return Currency(self.value-other.value,self.unit) if isinstance(other,Currency) else\
            Currency(self.value-other,self.unit)

    def __float__(self):
        return float(self.value)

    def __truediv__(self, other):
        return Currency(self.value/other,self.unit)

    def __rtruediv__(self, other):
        return Currency(other/self.value,self.unit)

    def update_cost(self,newCE,baseCE):
        return self*newCE/baseCE

    @classmethod
    def Economize(cls,f):
        def new_f(x):
            return cls(f(x))

        return new_f

    @classmethod
    def econ_func(cls,f):

        def new_f(*args):
            return cls(f(*args))

        return new_f
