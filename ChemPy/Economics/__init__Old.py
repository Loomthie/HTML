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

    def __add__(self, other):
        if isinstance(other,Currency):
            if self.unit != other.unit:
                raise ValueError()
            return Currency(self.value+other.value)
        return Currency(self.value+float(other),self.unit,self.mode)

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        return Currency(self.value*other,self.unit,self.mode)

    def __rmul__(self,other):
        return self.__mul__(other)

class Module:

    Lang_Cost = Currency(0)
    IF_Cost = Currency(0)
    Base_Cost = Currency(0)
    CE_Target = 809
    CE_Initial = 567

    def __init__(self,Name:str,Desc:str):
        self.Module_Name = Name
        self.Module_Description = Desc
        self.Updated_Lang_Cost = self.Lang_Cost*(self.CE_Target/self.CE_Initial)
        self.Updated_IF_Cost = self.IF_Cost*(self.CE_Target/self.CE_Initial)
        self.Updated_Base_Cost = self.Base_Cost*(self.CE_Target/self.CE_Initial)


class HeatExchanger(Module):

    fl_dict = {
        8:1.25,
        12:1.12,
        16:1.05,
        20:1.00
    }

    fd_dict = {
        'Fixed Head':0.85,
        'Kettle Vaporizer':1.35,
        'Floating Head':1.,
        'U Tube':0.85
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

    def __init__(self,Name,Desc,pres,tube_length,area,exchanger_type='Fixed Head',Fm=1.,Fbm=3.17):

        self.Fp = 0.9803+.018*(pres/100)+.0017*(pres/100)**2
        self.Fl = self.fl_dict[tube_length] if tube_length in self.fl_dict \
            else self.__fl_correlation(tube_length)
        baseCost = self.__cost_forms[exchanger_type](area)
        self.Base_Cost = Currency(baseCost)
        self.Fm = Fm
        self.Fbm = Fbm
        self.Fd = self.fd_dict[exchanger_type] if exchanger_type in self.fd_dict else 1.

        Lang_Cost = self.Fp*self.Fl*self.Fm*baseCost
        self.Lang_Cost = Currency(Lang_Cost)

        IF_Cost = baseCost*((self.Fbm-1)/self.Fd+(self.Fm*self.Fp*self.Fl))
        self.IF_Cost = Currency(IF_Cost)

        super().__init__(Name,Desc)


class Utilities:

    def __init__(self,steam_flow=0,elec_pow=0,cool_water=0,proc_water=0,refrig=0):
        self.steam = Currency(self.__steam_calc(steam_flow))
        self.elec = Currency(self.__elec_calc(elec_pow))
        self.cool_water = Currency(self.__cool_wat_calc(cool_water))
        self.proc_water = Currency(self.__proc_wat_calc(proc_water))
        self.refrigeration = Currency(self.__refridge_calc(refrig))
        self.total_cost = self.steam+self.elec+self.cool_water+self.proc_water+self.refrigeration

    @staticmethod
    def __steam_calc(steam):
        return 930*steam**.81

    @staticmethod
    def __elec_calc(s):
        return 2.9e6*s**0.83

    @staticmethod
    def __cool_wat_calc(s):
        return 1.1e3*s**0.68

    @staticmethod
    def __proc_wat_calc(s):
        return 1.7e3*s**0.96

    @staticmethod
    def __refridge_calc(s):
        return 12.5e3*s**0.77


class Economic_Report:

    class Operating_Costs:

        # (PSI,$)
        __steam_costs = {
            90:6.7
        }

        def __init__(self,Sales:Currency,Matl_Costs:Currency):
            pass

    def __init__(self,*Modules:Module,Sales:Currency|None=None,Util:Utilities | None = None, Project_Name='Economic Report',file_name:str | None = None):
        self.modules = Modules
        if not Util:
            Util = Utilities()

        if not Sales: Sales = Currency(0)

        self.Salse=Sales

        self.Utilities = Util
        self.totalEscBMCost = Currency(np.sum([a.Updated_IF_Cost.value for a in self.modules]))
        self.totalPurchaseCost = Currency(np.sum([a.Updated_Base_Cost.value for a in self.modules]))
        self.instAndControls = self.totalPurchaseCost*.55
        self.TBM_Cost = self.totalPurchaseCost+self.totalEscBMCost+self.instAndControls

        self.sitePrep = 0.05*self.TBM_Cost
        self.Service = 0.05*self.TBM_Cost

        self.DPI = self.TBM_Cost+self.sitePrep+self.Service+Util.total_cost
        self.contingency = 0.18*self.DPI
        self.TDC = self.DPI+self.contingency

        self.land = 0.02*self.TDC
        self.royalties = 0.02*self.TDC
        self.startUp = 0.1*self.TDC
        self.TPI = self.TDC+self.land+self.royalties+self.startUp

        self.WC = 0.15*self.TPI
        self.TCI = self.TPI + self.WC


e105 = HeatExchanger('E-105','',554,20,2250)
test = Economic_Report(e105)


