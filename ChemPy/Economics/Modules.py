import numpy as np
import pandas as pd
import plotly.graph_objects as go
from __correlations import fl_corr
from Currency import Currency


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
    LowAlloySteel= 'Low Alloy Steel'
    StainSteel304 = 'Stainless Steel 304'
    StainSteel316 = 'Stainless Steel 316'
    Carp20CB3 = 'Carpenter 20CB-3'
    Nickel200 = 'Nickel-200'
    Monel400 = 'Monel-400'
    Inconel600 = 'Inconel-600'
    Incoloy825 = 'Incoloy-825'


class Module:
    CE = 809
    baseCE = 567

    def __init__(self,Name:str,Desc:str):
        self.name = Name
        self.desc = Desc
        self.baseCost = self.base_cost_calc()
        self.bmCost = self.bm_cost_calc()

        self.updatedBaseCost = self.updated_cost(self.baseCost)
        self.updatedBmCost = self.updated_cost(self.bmCost)


    def base_cost_calc(self):
        return Currency(0)

    def bm_cost_calc(self):
        return Currency(0)

    def updated_cost(self,cost:Currency):
        return cost*(self.CE/self.baseCE)

    def __repr__(self):
        return f'''
    CE = {self.baseCE}
    Base Cost     = {self.baseCost}
    BM Cost       = {self.bmCost}

    CE = {self.CE}
    Base Cost     = {self.updatedBaseCost}
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

    def bm_cost_calc(self):
        return self.baseCost*(self.Fbm+(self.Fd*self.Fp*self.Fm-1))


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

        super().__init__(Name,Desc)

    @Currency.Economize
    def base_cost_calc(self):
        return self.__motor_cost + self.__pump_cost

    @Currency.Economize
    def bm_cost_calc(self):
        return self.baseCost * self.Fbm


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
        self.Ft = self.Ft_vals[TrayType]
        self.Fs = self.Fs_vals[TraySpacing]

        self.Cshell = np.exp(10.5449-0.4672*np.log(self.weight)+.05482*np.log(self.weight)**2)
        self.Cpl = 410*self.diameter**0.7396*self.length**0.70684
        self.Ctrays = 468*np.exp(0.1482*self.diameter)*self.nTrays*self.Fnt

        self.Fbm_trays = self.Ft+self.Fs+self.Fm

        super().__init__(Name,Desc)

    @Currency.Economize
    def base_cost_calc(self):
        return self.Cshell+self.Cpl+self.Ctrays

    @Currency.Economize
    def bm_cost_calc(self):
        shell = self.Cshell*(self.Fbm+(self.Fd*self.Fm*self.Fp-1))
        tray = self.Ctrays*self.Fbm_trays
        print(shell)
        return shell+tray+self.Cpl


class VesselOrientation:
    Horiz ='Horizontal'
    Vert = 'Vertical'


class Vessel(Module):

    Fm_dict = {
        Material.CarbonSteel:1.0,
        Material.Titanium:7.7,
        Material.LowAlloySteel:1.2,
        Material.StainSteel304:1.7,
        Material.StainSteel316:2.1,
        Material.Carp20CB3:3.2,
        Material.Nickel200:5.4,
        Material.Monel400:3.6,
        Material.Inconel600:3.9,
        Material.Incoloy825:3.7
    }

    Cv_calc = {
        VesselOrientation.Horiz: lambda W: np.exp(5.6336+0.4559*np.log(W)+.00582*np.log(W)**2),
        VesselOrientation.Vert: lambda W: np.exp(7.139+0.18255*np.log(W)+.02297*np.log(W)**2)
    }

    Cpl_calc = {
        VesselOrientation.Horiz:lambda D,L: 2275*D**0.2094,
        VesselOrientation.Vert:lambda D,L: 410*D**.73960*L**.70684
    }

    Fd = 1.0
    Fp = 1.0

    def __init__(self,Name,Desc,Diameter,Length,Weight,Orientation,Material):

        self.diameter = Diameter
        self.length = Length
        self.weight = Weight
        self.orientation=Orientation
        self.material = Material

        self.Fm = self.Fm_dict[self.material]
        self.Fbm = 3.05 if self.orientation == VesselOrientation.Horiz else 4.16

        self.Cshell = self.Cv_calc[Orientation](self.weight)
        self.Cpl = self.Cpl_calc[Orientation](self.diameter,self.length)

        super().__init__(Name,Desc)

    @Currency.Economize
    def base_cost_calc(self):
        return self.Cshell+self.Cpl

    @Currency.Economize
    def bm_cost_calc(self):
        return self.Cshell*(self.Fbm+(self.Fd*self.Fm*self.Fp-1)) + self.Cpl