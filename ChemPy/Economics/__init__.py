import pandas as pd
import numpy as np

class Currency:

    def __init__(self,value,unit='$',mode=0):
        self.value = value
        self.unit = unit
        self.mode = mode

    def __repr__(self):
        return f'{self.unit}{self.value/10**(3*self.mode):0.2f} {"".join(self.mode*["M"])}' \
    if self.value >= 0 else f'({self.unit}{self.value/10**(3*self.mode):0.2f}) {"".join(self.mode*["M"])}'


class Module:

    def __init__(self):
        pass


class HeatExchanger(Module):

    fl_dict = {
        8:1.25,
        12:1.12,
        16:1.05,
        20:1.00
    }

    __cost_forms = {
        'Fixed Head': lambda a: np.exp(11.4815-0.9228*np.log(a)+.09861*(np.log(a)**2)),
        'Floating Head': lambda a: np.exp(12.0310 - .8709 * np.log(a) + .09005 * (np.log(a)) ** 2),
        'U Tube': lambda a: np.exp(11.5510 - .9186 * np.log(a) + .09790 * (np.log(a)) ** 2),
        'Kettle Vaporizer': lambda a: np.exp(12.3310 - .8709 * np.log(a) + .09005 * (np.log(a)) ** 2)
    }

    @staticmethod
    def __fl_correlation(fl):
        return np.exp(0.35320481)*np.exp(-fl*0.01834923)

    def __init__(self,pres,tube_length,area,exchanger_type='Fixed Head',Fm=1.):

        self.Fp = 0.9803+.018*(pres/100)+.0017*(pres/100)**2
        self.Fl = self.fl_dict[tube_length] if tube_length in self.fl_dict \
            else self.__fl_correlation(tube_length)
        self.baseCost = self.__cost_forms[exchanger_type](area)
        self.Fm = Fm

        Lang_Cost = self.Fp*self.Fl*self.Fm*self.baseCost
        self.Lang_Cost = Currency(Lang_Cost)

        super().__init__()