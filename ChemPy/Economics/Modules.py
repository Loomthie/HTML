from ChemPy.Economics.Currency import Currency
from ChemPy.Economics.Materials import Catalyst,SteamStream
import xlwings as xl
import numpy as np


class Module:
    Fbm = 1.0
    Fp = 1.0
    Fd = 1.0
    Fm = 1.0
    corrCE = 567
    xlHeader=[]

    def __init__(self,name:str,desc:str):

        self.name = name
        self.desc = desc

        self.baseCost = self.base_cost_calc()
        self.purchCost = self.purch_cost_calc()
        self.bmCost = self.bm_cost_calc()

        self.xlNameRange = self.name.replace('-', '')

    def generate_row_xl(self):
        return self.baseCost,self.purchCost,self.bmCost

    def generate_formulas_xl(self,sh:xl.Sheet,row):
        return []

    @Currency.econ_func
    def base_cost_calc(self):
        return 0

    @Currency.econ_func
    def purch_cost_calc(self):
        return 0

    @Currency.econ_func
    def bm_cost_calc(self):
        return self.purchCost*(self.Fbm+(self.Fd*self.Fm*self.Fp-1))


# region Pump
class Pump(Module):

    Fbm = 3.30
    xlHeader=['Name','Flow','Head','Size Factor','Pump Cost','Pump Power','Pump Efficiency','Brake Power',
              'Motor Efficiency','Power Consumption','Motor Cost','Cb','Cp','Fbm','Fm','Fd','Fp','Cbm']

    def __init__(self,name:str,desc:str,flow_rate:float,pump_power:float,type_factor_pump:float=1.0,
                 type_factor_motor:float=1.0,**kwargs):

        for key,val in kwargs.items():self.__dict__[key]=val

        self.Q = flow_rate
        self.Pt = pump_power
        self.Ft = type_factor_pump
        self.motorFt = type_factor_motor

        self.etaP = -0.316+0.24015*np.log(self.Q)-0.01199*np.log(self.Q)**2
        self.Pb = self.Pt/self.etaP
        self.etaM = 0.8+0.0319*np.log(self.Pb)-0.00182*np.log(self.Pb)**2
        self.Pc = self.Pt/self.etaP/self.etaM

        self.motorBaseCost = self.motor_base_cost_calc()
        self.motorPurchCost = self.motor_purch_cost_calc()
        self.pumpBaseCost = self.pump_base_cost_calc()
        self.pumpPurchCost = self.pump_purch_cost_calc()

        super().__init__(name,desc)

    def generate_row_xl(self):
        return [self.name,self.Q,'\'--','\'--',self.pumpPurchCost,self.Pt,self.etaP,self.Pb,self.etaM,self.Pc,self.motorPurchCost,
                self.baseCost,self.purchCost,self.Fbm,self.Fd,self.Fm,self.Fp,self.bmCost]

    def generate_formulas_xl(self,sh:xl.Sheet,row):

        sh.range(f'R{row}').name = f'BM_{self.xlNameRange}'
        sh.range(f'M{row}').name = f'CP_{self.xlNameRange}'

        currency = [0,0,0,0,1,0,0,0,0,0,1,1,0,0,0,0,0,1]

        return [self.name,self.Q,'\'--',f'\'--',
                f'=EXP(12.1656-1.1448*LN(D{row})+0.0862*LN(D{row})^2)*{self.Ft}*{self.Fm}',
                self.Pt,f'=-0.316+0.24015*LN(B{row})-0.01199*LN(B{row})^2',f'=F{row}/G{row}',
                f'=0.8+0.0319*LN(H{row})-0.00182*LN(H{row})^2',f'=F{row}/G{row}/I{row}',
                f'=EXP(5.9332+0.16829*LN(J{row})-0.110056*LN(J{row})^2+0.071413*LN(J{row})^3-.0063788*LN(J{row})^4)*{self.motorFt}',
                f'=E{row}/{self.Ft}/{self.Fm}+K{row}/{self.motorFt}',f'=E{row}+K{row}',self.Fbm,self.Fm,self.Fd,self.Fp,
                f'=M{row}*(N{row}+(O{row}*P{row}*Q{row}-1))'],currency

    @Currency.econ_func
    def motor_base_cost_calc(self):
        return np.exp(5.9332+0.16829*np.log(self.Pc)-0.110056*np.log(self.Pc)**2+\
                      0.071413*np.log(self.Pc)**3-0.0063788*np.log(self.Pc)**4)

    @Currency.econ_func
    def motor_purch_cost_calc(self):
        return self.motorBaseCost*self.motorFt

    @Currency.econ_func
    def pump_base_cost_calc(self):
        return 0

    @Currency.econ_func
    def pump_purch_cost_calc(self):
        return self.pumpBaseCost*self.Ft*self.Fm

    @Currency.econ_func
    def base_cost_calc(self):
        return self.pumpBaseCost+self.motorBaseCost

    @Currency.econ_func
    def purch_cost_calc(self):
        return self.pumpPurchCost+self.motorPurchCost


class CentrifugalPump(Pump):

    def __init__(self,name,desc,flow_rate,pump_power,head:float,type_factor=1.0,motor_type_factor=1.0,**kwargs):

        self.S = flow_rate * np.sqrt(head) # size factor
        self.H = head

        super().__init__(name,desc,flow_rate,pump_power,type_factor,motor_type_factor,**kwargs)

    @Currency.econ_func
    def pump_base_cost_calc(self):
        return np.exp(12.1656-1.1448*np.log(self.S)+0.0862*np.log(self.S)**2)

    def generate_row_xl(self):
        res = super().generate_row_xl()
        res[2] = self.H
        res[3] = self.S
        return res

    def generate_formulas_xl(self,sh:xl.Sheet,row):
        res = super().generate_formulas_xl(sh,row)
        res[0][2]=self.H
        res[0][3]=f'=B{row}*SQRT(C{row})'
        return res


class ExternalGearPump(Pump):

    @Currency.econ_func
    def pump_base_cost_calc(self):
        return np.exp(8.2816-0.2918*np.log(self.Q)+0.0743*np.log(self.Q)**2)


class ReciprocatingPlungerPump(Pump):

    @Currency.econ_func
    def pump_base_cost_calc(self):
        return np.exp(7.9361+0.26986*np.log(self.Pb)+0.06718*np.log(self.Pb)**2)
# endregion


# region Compressor
class Compressor(Module):

    xlHeader = ['Name','Pt','ηP','ηM','Pc','Cb','Cp','Fbm','Fm','Fd','Fp','Cbm']
    Fbm = 2.15

    def __init__(self,name,desc,pump_power,comp_eff=0.75,motor_eff=1.0,**kwargs):
        for key,val in kwargs.items(): self.__dict__[key]=val
        self.Pt = pump_power
        self.etaP = comp_eff
        self.etaM = motor_eff
        self.Pc = self.Pt/self.etaP/self.etaM
        super().__init__(name,desc)

    @Currency.econ_func
    def purch_cost_calc(self):
        return self.baseCost*self.Fd*self.Fm

    def generate_row_xl(self):
        return [self.name,self.Pt,self.etaP,self.etaM,self.Pc,self.baseCost,self.purchCost,
                self.Fbm,self.Fm,self.Fd,self.Fp,self.bmCost]

    def generate_formulas_xl(self,sh:xl.Sheet,row):

        a = self.name
        b = self.Pt
        c = self.etaP
        d = self.etaM
        e = f'=B{row}/C{row}/D{row}'
        f = '' # i = 5
        g = f'=F{row}*{self.Fm}*{self.Fd}'
        h = self.Fbm
        i = self.Fm
        j = self.Fd
        k = self.Fp
        l = f'=G{row}*(H{row}+(I{row}*J{row}*K{row}-1))'

        sh.range(f'G{row}').name = f'CP_{self.xlNameRange}'
        sh.range(f'L{row}').name = f'BM_{self.xlNameRange}'

        cur = [0,0,0,0,0,1,1,0,0,0,0,1]
        res = [a,b,c,d,e,f,g,h,i,j,k,l]

        return res,cur


class CentrifugalCompressor(Compressor):

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(9.1553+0.63*np.log(self.Pc))

    def generate_formulas_xl(self,sh:xl.Sheet,row):
        res,cur = super().generate_formulas_xl(sh,row)
        res[5] = f'=EXP(9.1553+0.63*LN(E{row}))'
        return res,cur


class ReciprocatingCompressor(Compressor):

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(4.6762+1.23*np.log(self.Pc))

    def generate_formulas_xl(self,sh:xl.Sheet,row):
        res,cur = super().generate_formulas_xl(sh,row)
        res[5]=f'=EXP(4.6762+1.23*LN(E{row}))'
        return res,cur


class ScrewCompressor(Compressor):

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(8.2496+0.7243*np.log(self.Pc))

    def generate_formulas_xl(self,sh:xl.Sheet,row):
        res,cur = super().generate_formulas_xl(sh,row)
        res[5]=f'=EXP(8.2496+0.7243*LN(E{row}))'
        return res,cur
# endregion

#region Fan
class Fan(Module):

    def __init__(self,name,desc,head_factor:float,flow_rate:float,
                 head:float,fan_eff=0.7,motor_eff=0.9,**kwargs):

        for key,val in kwargs.items(): self.__dict__[key]=val

        self.Fh = head_factor
        self.Q = flow_rate
        self.H = head
        self.etaF = fan_eff
        self.etaM = motor_eff

        self.Pc = self.Q * self.H / (6350*self.etaF*self.etaM)

        super().__init__(name,desc)

    @Currency.econ_func
    def purch_cost_calc(self):
        return self.baseCost*self.Fh*self.Fm

    def generate_row_xl(self):
        return [self.name,self.Q,self.H,self.Fh,self.etaF,self.etaM,self.Pc,self.baseCost,self.purchCost,
                self.Fbm,self.Fm,self.Fd,self.Fp,self.bmCost]


class CentrifugalBackwardFan(Fan):

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(11.4152-1.3805*np.log(self.Q)+0.1139*np.log(self.Q)**2)


class CentrifugalStraightFan(Fan):
    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(12.1667-1.6407*np.log(self.Q)+0.1328*np.log(self.Q)**2)


class VaneAxialFan(Fan):

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(9.6487-0.97566*np.log(self.Q)+0.08532*np.log(self.Q)**2)


class PropellerFan(Fan):

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(6.16328-0.28635*np.log(self.Q)+0.04866*np.log(self.Q)**2)
#endregion

# region Heat Exchanger/Fired Heater


class HeatExchanger(Module):

    Fbm = 3.17
    fl_dict = {
        8:1.25,
        12:1.12,
        16:1.05,
        20:1.0
    }

    twVolFlow = 0  # gpm
    twMassFlow = 0  # lb/h
    steamStream = SteamStream(0, 0, 0)

    baseCostXlFormula = ''

    xlHeader = ['Name','P','Fp','Tube Length','Area','Fl','Fbm','Fm','Fd','Cb','Cp','Cbm']

    def __init__(self,name,desc,tube_length,pressure,area,a=0.0,b=0.0,**kwargs):
        for key,value in kwargs.items():self.__dict__[key]=value

        self.tubeLength = tube_length
        self.P = pressure
        self.A = area

        self.Fm = a+(self.A/100)**b
        self.Fl = self.fl_func(tube_length) if tube_length not in self.fl_dict else self.fl_dict[tube_length]
        self.Fp = 0.9803+0.018*(self.P/100)+0.0017*(self.P/100)**2

        self.Fp = self.Fp if self.Fp > 1 else 1

        super().__init__(name,desc)

    @Currency.econ_func
    def purch_cost_calc(self):
        return self.Fp*self.Fm*self.Fl*self.baseCost

    def generate_row_xl(self):
        return [self.name,self.P,self.Fp,self.tubeLength,self.A,self.Fl,
                self.Fbm,self.Fm,self.Fd,self.baseCost,self.purchCost,self.bmCost]

    def generate_formulas_xl(self,sh:xl.Sheet,row):

        a = self.name
        b = self.P
        c = self.Fp
        d = self.tubeLength
        e = self.A
        f = self.Fl
        g = self.Fbm
        h = self.Fm
        i = self.Fd
        j = self.baseCostXlFormula.format(row=row)
        k = f'=C{row}*h{row}*F{row}*j{row}'
        l = f'=k{row}*(g{row}+(h{row}*h{row}*c{row}-1))'

        res = [a,b,c,d,e,f,g,h,i,j,k,l]
        cur = [0,0,0,0,0,0,0,0,0,1,1,1]

        return res,cur

    @staticmethod
    def fl_func(L):
        tl = np.array([8, 12, 16, 20])
        fl = np.array([1.25, 1.12, 1.05, 1.00])

        fl_y = fl * tl
        fl_x = np.array([tl, np.ones_like(tl), -fl]).T

        res_fl = np.linalg.solve(fl_x.T @ fl_x, fl_x.T @ fl_y)
        res_fl[1] -= res_fl[0] * res_fl[2]

        def fl_corr(L):
            return res_fl[0] + res_fl[1] / (L + res_fl[2])

        return round(fl_corr(L),2)


class FloatingHeadHx(HeatExchanger):

    baseCostXlFormula = '=EXP(12.0310-0.8709*LN(E{row})+0.09005*LN(E{row})^2)'

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(12.0310-0.8709*np.log(self.A)+0.09005*np.log(self.A)**2)


class FixedHeadHx(HeatExchanger):

    Fd=0.85

    baseCostXlFormula = '=EXP(11.4185-0.9228*LN(E{row})+0.09861*LN(E{row})^2)'

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(11.4185-0.9228*np.log(self.A)+0.09861*np.log(self.A)**2)


class UtubeHx(HeatExchanger):

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(11.5510-0.9186*np.log(self.A)+0.09790*np.log(self.A)**2)


class KettleHx(HeatExchanger):

    Fd = 1.35
    baseCostXlFormula = '=EXP(12.3310-0.8709*LN(E{row})+0.09005*LN(E{row})^2)'

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(12.3310-0.8709*np.log(self.A)+0.09005*np.log(self.A)**2)


class FiredHeater(Module):

    ngFlow = 0
    Fbm = 2.19
    xlHeader = ['Name','P','Fp','Q','Fbm','Fm','Fd','Cb','Cp','Cbm']

    def __init__(self,name,desc,heat_duty,pressure,**kwargs):
        for key,value in kwargs.items(): self.__dict__[key]=value
        self.Q = heat_duty
        self.P = pressure
        self.Fp = 0.986-0.0035*(self.P/500)+0.0175*(self.P/500)**2
        super().__init__(name,desc)

    @Currency.econ_func
    def base_cost_calc(self):
        return np.exp(-0.15241+0.785*np.log(self.Q))

    @Currency.econ_func
    def purch_cost_calc(self):
        return self.Fp*self.Fm*self.baseCost

    def generate_row_xl(self):
        return [self.name,self.P,self.Fp,self.Q,
                self.Fbm,self.Fm,self.Fd,self.baseCost,self.purchCost,self.bmCost]

    def generate_formulas_xl(self,sh:xl.Sheet,row):

        a = self.name
        b = self.P
        c = f'=0.986-0.0035*(b{row}/500)+0.0175*(b{row}/500)^2'
        d = self.Q
        e = self.Fbm
        f = self.Fm
        g = self.Fd
        h = f'=EXP(-0.15241+0.785*LN(d{row}))'
        i = f'=c{row}*f{row}*h{row}'
        j = f'=i{row}*(e{row}+(c{row}*f{row}*g{row}-1))'

        res = [a,b,c,d,e,f,g,h,i,j]
        cur = [0,0,0,0,0,0,0,1,1,1]

        return res,cur
# endregion


# region Vessel
class Vessel(Module):

    def __init__(self,name,desc,weight,inside_diameter,**kwargs):
        for key,val in kwargs.items(): self.__dict__[key]=val

        self.Di = inside_diameter
        self.W = weight

        self.Cv = self.shell_cost_calc()
        self.Cpl = self.pl_cost_calc()

        super().__init__(name,desc)

    @Currency.econ_func
    def pl_cost_calc(self):
        return 0

    @Currency.econ_func
    def shell_cost_calc(self):
        return 0

    @Currency.econ_func
    def purch_cost_calc(self):
        return self.Fm*self.Cv+self.Cpl

    @Currency.econ_func
    def bm_cost_calc(self):
        return self.Cv/self.Fm*(self.Fbm+(self.Fm*self.Fd*self.Fp-1))+self.Cpl


class HorizontalVessel(Vessel):

    xlHeader = ['Name','D','W','Fbm','Fd','Fm','Fp','Cv','Cpl','Cbm']
    Fbm=3.05

    @Currency.econ_func
    def shell_cost_calc(self):
        return np.exp(5.6336+0.4599*np.log(self.W)+0.00582*np.log(self.W)**2)*self.Fm

    @Currency.econ_func
    def pl_cost_calc(self):
        return 2275*self.Di**0.2094

    def generate_row_xl(self):
        return [self.name,self.Di,self.W,self.Fbm,self.Fd,self.Fm,self.Fp,self.Cv,self.Cpl,self.bmCost]

    def generate_formulas_xl(self,sh:xl.Sheet,row):

        sh.range(f'H{row}').name=f'CP_{self.xlNameRange}'
        sh.range(f'J{row}').name=f'BM_{self.xlNameRange}'

        a = self.name
        b = self.Di
        c = self.W
        d = self.Fbm
        e = self.Fd
        f = self.Fm
        g = self.Fp
        h = f'=EXP(5.6336+0.4599*LN(c{row})+.00582*LN(c{row})^2)*f{row}'
        i = f'=2275*b{row}^0.2094'
        j = f'=h{row}/f{row}*(d{row}+(e{row}*f{row}*g{row}-1))+i{row}'

        res = [a,b,c,d,e,f,g,h,i,j]
        cur = [0,0,0,0,0,0,0,1,1,1]

        return res,cur


class VerticalVessel(Vessel):
    Fbm = 4.16

    xlHeader = ['Name','D','L','W','Fbm','Fm','Fd','Fp','Cv','Cpl','Cbm']

    def __init__(self,name,desc,weight,inside_diameter,length,**kwargs):

        self.L = length

        super().__init__(name,desc,weight,inside_diameter,**kwargs)

    @Currency.econ_func
    def shell_cost_calc(self):
        return np.exp(7.1390+0.18255*np.log(self.W)+0.02297*np.log(self.W)**2)*self.Fm

    @Currency.econ_func
    def pl_cost_calc(self):
        return 410*self.Di**0.7396*self.L**0.70684

    def generate_row_xl(self):
        return [self.name,self.Di,self.L,self.W,self.Fbm,self.Fm,
                self.Fd,self.Fp,self.Cv,self.Cpl,self.bmCost]

    def generate_formulas_xl(self,sh:xl.Sheet,row):

        sh.range(f'i{row}').name=f'CP_{self.xlNameRange}'
        sh.range(f'k{row}').name=f'BM_{self.xlNameRange}'

        a = self.name
        b = self.Di
        c = self.L
        d = self.W
        e = self.Fbm
        f = self.Fm
        g = self.Fd
        h = self.Fp
        i = f'=EXP(7.139+0.18255*LN(d{row})+0.02297*LN(d{row})^2)*f{row}'
        j = f'=410*b{row}^0.7396*c{row}^0.70684'
        k = f'=i{row}/f{row}*(e{row}+(f{row}*g{row}*h{row}-1))+j{row}'

        res = [a,b,c,d,e,f,g,h,i,j,k]
        cur = [0,0,0,0,0,0,0,0,1,1,1]

        return res,cur


class Column(Module):

    Fbm = 4.16
    xlHeader = ['Name','D','L','W','N','Fnt','Fbm (Trays)','Fbm (Tower)',
                'Fm','Fd','Fp','Cv','Cpl','Ctrays','Ctower','Cbm']

    class Trays:

        Fs_dict = {
            24:1,
            18:1.4,
            12:2.2
        }
        Ft_dict = {
            'Sieve':0,
            'Valve':0.4,
            'Bubble Cap':1.8
        }

        def __init__(self,num_trays,tray_spacing=24,tray_type='Sieve',Fm=1.0):
            self.N = num_trays
            self.traySpace = tray_spacing
            self.trayType = tray_type
            self.Fm = Fm

            self.Fnt = 1 if self.N > 20 else 2.25/1.0414**self.N
            self.Fs = self.Fs_dict[tray_spacing]
            self.Ft = self.Ft_dict[tray_type]

            self.Fbm = self.Fm+self.Fs+self.Ft

    def __init__(self,name,desc,diameter,length,weight,trays:Trays,**kwargs):

        for key,val in kwargs.items(): self.__dict__[key] = val

        self.D = diameter
        self.L = length
        self.W = weight
        self.trays = trays

        self.trayFactor = self.trays.N*self.trays.Fnt*self.trays.Fm

        self.Cv = Currency(np.exp(10.5449-0.4672*np.log(self.W)+0.05482*np.log(self.W)**2))*self.Fm
        self.Cpl = Currency(341*self.D**0.63316*self.L**0.80161)
        self.Ctrays = Currency(468*np.exp(0.1482*self.D))*self.trayFactor

        super().__init__(name,desc)

    def base_cost_calc(self):
        return self.Cv/self.Fm+self.Cpl+self.Ctrays/self.trayFactor

    def purch_cost_calc(self):
        return self.Cv+self.Cpl+self.Ctrays

    def bm_cost_calc(self):
        return self.Cv/self.Fm*(self.Fbm+(self.Fm*self.Fd*self.Fp-1))+self.Cpl+self.Ctrays*self.trays.Fbm

    def generate_row_xl(self):
        return [self.name,self.D,self.L,self.W,self.trays.N,self.trays.Fnt,self.trays.Fbm,self.Fbm,self.Fm,self.Fd,
                self.Fp,self.Cv,self.Cpl,self.Ctrays,self.purchCost,self.bmCost]

    def generate_formulas_xl(self,sh:xl.Sheet,row):

        sh.range(f'o{row}').name = f'CP_{self.xlNameRange}'
        sh.range(f'p{row}').name = f'BM_{self.xlNameRange}'

        a = self.name
        b = self.D
        c = self.L
        d = self.W
        e = self.trays.N
        f = f'=MAX(1,2.25/1.0414^e{row})'
        g = self.trays.Fbm
        h = self.Fbm
        i = self.Fm
        j = self.Fd
        k = self.Fp
        l = f'=EXP(10.5449-0.4672*LN(d{row})+0.05482*LN(d{row})^2)*i{row}'
        m = f'=341*b{row}^0.63316*c{row}^0.80161'
        n = f'=468*EXP(0.1482*b{row})*{self.trayFactor}'
        o = f'=l{row}+m{row}+n{row}'
        p = f'=l{row}/i{row}*(h{row}+(i{row}*j{row}*k{row}-1))+m{row}+n{row}*g{row}'

        res = [a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p]
        cur = [0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1]

        return res,cur


class HorizontalReactor(HorizontalVessel):

    def __init__(self,name,desc,weight,inside_diameter,catalyst:Catalyst,**kwargs):

        self.catalyst = catalyst

        super().__init__(name,desc,weight,inside_diameter,**kwargs)


class VerticalReactor(VerticalVessel):

    def __init__(self,name,desc,weight,inside_diameter,length,catalyst:Catalyst,**kwargs):
        self.catalyst = catalyst
        super().__init__(name,desc,weight,inside_diameter,length,**kwargs)
# endregion


# region Tanks
class Tank(Module):

    xlHeader = ['Name','Volume','Ctank','Fbm','Fm','Fd','Fp','Cbm']

    corrCE = 567
    Fbm=4.16

    def __init__(self,name,desc,volume,**kwargs):
        for key,value in kwargs.items(): self.__dict__[key]=value

        self.volume = volume

        super().__init__(name,desc)

    def generate_row_xl(self):
        return [self.name,self.volume,self.purchCost,self.Fbm,self.Fm,
                self.Fd,self.Fp,self.bmCost]


class OpenTank(Tank):

    @Currency.econ_func
    def purch_cost_calc(self):
        return 18*self.volume**0.73


class ConeRoofTank(Tank):

    @Currency.econ_func
    def purch_cost_calc(self):
        return 265*self.volume**0.513


class FloatingRoofTank(Tank):

    @Currency.econ_func
    def purch_cost_calc(self):
        return 475*self.volume**.507


class SphericalLPTank(Tank):

    @Currency.econ_func
    def purch_cost_calc(self):
        return 68*self.volume**0.72


class SphericalHPTank(Tank):

    @Currency.econ_func
    def purch_cost_calc(self):
        return 53*self.volume**0.78


class GasHoldersTank(Tank):

    @Currency.econ_func
    def purch_cost_calc(self):
        return 3595*(self.volume*7.48052)**0.43
# endregion
