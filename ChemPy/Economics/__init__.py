import numpy as np
import pandas as pd
import plotly.graph_objects as go
from __correlations import fl_corr


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

    @classmethod
    def Economize(cls,f):
        def new_f(x):
            return cls(f(x))

        return new_f


class Material:
    CarbonSteel = 'Carbon Steel'
    Copper = 'Copper'
    StainlessSteel = 'Stainless Steel'
    Nickel = 'Nickel'
    Titanium = 'Titanium'
    Brass = 'Brass'
    Monel = 'Monel'
    CrMoSteel = 'Cr-Mo Steel'
    CastIron = 'Cast Iron'
    DuctIron = 'Ductile Iron'
    CastSteel = 'Cast Steel'
    Bronze = 'Bronze'
    HastelloyC = 'Hastelloy C'


class Module:
    CE = 809
    baseCE = 567

    def __init__(self,Name:str,Desc:str):
        self.name = Name
        self.desc = Desc
        self.baseCost = self.base_cost_calc()
        self.purchCost = self.purch_cost_calc()
        self.bmCost = self.bm_cost_calc()

        self.updatedBaseCost = self.updated_cost(self.baseCost)
        self.updatedPurchCost = self.updated_cost(self.purchCost)
        self.updatedBmCost = self.updated_cost(self.bmCost)


    def base_cost_calc(self):
        return Currency(0)

    def bm_cost_calc(self):
        return Currency(0)

    def purch_cost_calc(self):
        return Currency(0)

    def updated_cost(self,cost:Currency):
        return cost*(self.CE/self.baseCE)

    def __repr__(self):
        return f'''
    CE = {self.baseCE}
    Base Cost     = {self.baseCost}
    Purchase Cost = {self.purchCost}
    BM Cost       = {self.bmCost}

    CE = {self.CE}
    Base Cost     = {self.updatedBaseCost}
    Purchase Cost = {self.updatedPurchCost}
    BM Cost       = {self.updatedBmCost}
'''


class HeatExchangerType:
    Fixed_Head = 'Fixed Head'
    Floating_Head = 'Floating Head'
    U_Tube = 'U Tube'
    Kettle = 'Kettle'


class HeatExchanger(Module):
    Fm_coeffs = pd.DataFrame({
        Material.CarbonSteel:[(0,0),(1.08,.05),(1.75,0.13),(2.1,1.13),(5.2,0.16),(1.55,0.05)],
        Material.Brass:[(1.08,.05),*5*[np.NaN]],
        Material.StainlessSteel:[(1.75,0.13),np.NaN,(2.7,.07),*3*[np.NaN]],
        Material.Monel:[(2.1,0.13),*2*[np.NaN],(3.3,.08),*2*[np.NaN]],
        Material.Titanium:[(5.2,.016),*3*[np.NaN],(9.6,.06),np.NaN],
        Material.CrMoSteel:[(1.55,.05),*4*[np.NaN],(1.70,.07)]
    },index=[Material.CarbonSteel,Material.Brass,Material.StainlessSteel,Material.Monel,Material.Titanium,Material.CrMoSteel])
    Fbm = 3.17
    Fd_vals = {
        HeatExchangerType.Fixed_Head:0.85,
        HeatExchangerType.Floating_Head:1.00,
        HeatExchangerType.Kettle:1.35,
        HeatExchangerType.U_Tube:0.85
    }

    def __init__(self,Name,Desc,Pressure:float,Tube_Length:float,Area:float,
                 Matl_A:str,Matl_B:str,Hx_Type:str):

        self.pres = Pressure
        self.tubeLength = Tube_Length
        self.material = [Matl_A,Matl_B]
        self.area = Area
        self.hxType = Hx_Type

        self.Fd = self.Fd_vals[Hx_Type]
        self.Fp = 0.9803 + 0.018 * Pressure / 100 + .0017 * (Pressure / 100) ** 2
        self.Fl = fl_corr(self.tubeLength)
        self.Fm = self.Fm_coeffs.loc[*self.material][0] + (self.area / 100) ** self.Fm_coeffs.loc[*self.material][1]

        super().__init__(Name,Desc)

    @Currency.Economize
    def base_cost_calc(self):

        hx = HeatExchangerType()

        coeffs = {
            hx.Floating_Head:[12.0310,0.8709,0.09005],
            hx.Fixed_Head:[11.4185,0.9228,0.09861],
            hx.U_Tube:[11.5510,0.9186,0.09790],
            hx.Kettle:[12.3310,0.8709,0.09005]
        }

        def base_calc(A,a,b,c):
            return np.exp(a-b*np.log(A)+c*np.log(A)**2)

        return base_calc(self.area,*coeffs[self.hxType])

    @Currency.Economize
    def bm_cost_calc(self):
        return self.purchCost*(self.Fbm+(self.Fd*self.Fm*self.Fp-1))

    @Currency.Economize
    def purch_cost_calc(self):
        return self.Fp*self.Fm*self.Fl*self.baseCost


class Pump(Module):

    Fm_vals = {
        Material.CastIron:1.,
        Material.DuctIron:1.15,
        Material.CastSteel:1.35,
        Material.Bronze:1.9,
        Material.StainlessSteel:2.0,
        Material.HastelloyC:2.95,
        Material.Monel:3.3,
        Material.Nickel:3.5,
        Material.Titanium:9.70
    }

    Fbm = 3.30

    def __init__(self, Name, Desc, Q, H, FT_pump, FT_motor, PT, Matl:str):
        self.flow = Q
        self.height = H
        self.pumpPower = PT
        self.material = Matl

        self.size_fac = self.flow*self.height ** 0.5
        self.FT_pump = FT_pump
        self.FT_motor = FT_motor
        self.Fm = self.Fm_vals[self.material]
        self.etaP = -0.316+0.24015*np.log(self.flow)-0.01199*np.log(self.flow)**2
        self.pumpBreak = self.pumpPower/self.etaP
        self.etaM = 0.8+.0319*np.log(self.pumpBreak)-.00182*np.log(self.pumpBreak)**2
        self.powerConsumption = self.pumpPower/(self.etaP*self.etaM)

        self.__motor_cost = np.exp(5.9332+0.16829*np.log(self.powerConsumption)-.110056*np.log(self.powerConsumption)**2\
                                 +.071413*np.log(self.powerConsumption)**3-.0063788*np.log(self.powerConsumption)**4)
        self.__pump_cost = np.exp(12.1656-1.1448*np.log(self.size_fac)+.0862*np.log(self.size_fac)**2)

        print(self.etaM)

        super().__init__(Name,Desc)

    @Currency.Economize
    def base_cost_calc(self):
        return self.__motor_cost + self.__pump_cost

    @Currency.Economize
    def purch_cost_calc(self):
        return self.__motor_cost*self.FT_motor + self.__pump_cost*self.FT_pump*self.Fm

    @Currency.Economize
    def bm_cost_calc(self):
        return self.purchCost * self.Fbm


class TrayTypes:
    Sieve='Sieve'
    Valve='Valve'
    BubbleCap='Bubble Cap'


class Column(Module):

    Fbm = 4.16
    Ftm = 1.0
    Fm = 1.0
    Fd=1.0
    Fp=1.0

    Ft_vals = {
        TrayTypes.Sieve:0.,
        TrayTypes.Valve:0.4,
        TrayTypes.BubbleCap:1.8
    }

    Ftt_vals = {
        TrayTypes.Sieve:1.,
        TrayTypes.Valve:1.18,
        TrayTypes.BubbleCap:1.87
    }

    Fs_vals = {
        24:1,
        18:1.4,
        12:2.2
    }

    def __init__(self,Name,Desc,Diameter,Length,Weight,nTrays,TrayType,TraySpacing):

        self.diameter=Diameter
        self.length=Length
        self.weight=Weight
        self.nTrays=nTrays

        self.Fnt = 1 if self.nTrays >= 20 else 2.25/(1.0414**self.nTrays)
        self.Ftt = self.Ftt_vals[TrayType]

        self.Cshell = np.exp(10.5449-0.4672*np.log(self.weight)+.05482*np.log(self.weight)**2)
        self.Cpl = 341*self.diameter**0.63316*self.length**0.80161
        self.Ctrays = 468*np.exp(0.1482*self.diameter)

        self.Fbm_trays = self.Ft_vals[TrayType]+self.Fs_vals[TraySpacing]+self.Fm

        super().__init__(Name,Desc)

    @Currency.Economize
    def base_cost_calc(self):
        return self.Cshell+self.Cpl+self.Ctrays

    @Currency.Economize
    def purch_cost_calc(self):
        return self.nTrays*self.Fnt*self.Ftt*self.Ftm*self.Ctrays+self.Cshell+self.Cpl

    @Currency.Economize
    def bm_cost_calc(self):
        return self.Cshell*(self.Fbm+(self.Fd+self.Fm+self.Fp)) + self.nTrays*self.Fnt*self.Ftt*self.Ftm*self.Ctrays* \
               self.Fbm_trays+self.Cpl


test_col = Column('CL-200','',2,32,391,6,TrayTypes.Sieve,24)
print(test_col)