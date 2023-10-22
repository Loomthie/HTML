import xlwings as xl
from ChemPy.Economics.Modules import *
from ChemPy.Economics.Currency import Currency
import datetime


class Report:

    def __init__(self, Report_Name: str = 'ECONOMIC REPORT',Process_Modules:list[Module]=()):

        self.reportName = Report_Name
        self.modules = Process_Modules

        self.wb = xl.Book()

        self.capitalCost = CapitalCostBuildUp(self.modules)
        self.capital_sh = self.capitalCost.build_sheet(self.wb,self.reportName)
        self.equip_sh = self.__build_equipment_list()

    def __build_sheet_header(self,sh,title):
        sh.cells[0, 0].value = title
        sh.cells[1, 0].value = self.reportName.upper()
        sh.cells[2, 0].value = '\'' + datetime.date.today().strftime('%d %B %Y').upper()
        for r in range(3):
            sh.cells[r,0].font.bold=True

    def __build_equipment_list(self):

        sh = self.wb.sheets.add('Equipment List')
        self.__build_sheet_header(sh,'EQUIPMENT LIST')

        row = 4
        cols = ['Name','Description']
        for c in range(len(cols)):
            sh.cells[row,c].value=cols[c]
            sh.cells[row,c].font.bold=True
        row += 1

        for m in self.modules:
            cols = [m.name,m.desc]
            for c in range(len(cols)):
                sh.cells[row,c].value = cols[c]
            row += 1

        return sh


class ReportSection:
    row = 0

    def build_sheet(self,wb:xl.Book,sh_name,title,report_title):

        sh = wb.sheets.add(sh_name,after=wb.sheets[-1])

        sh.cells[0,0].value = title
        sh.cells[0,0].font.bold = True

        sh.cells[1,0].value = report_title
        sh.cells[1,0].font.bold = True

        sh.cells[2,0].value = '\' UPDATED ON '+datetime.date.today().strftime('%D %B %Y')
        sh.cells[2,0].font.bold = True

        return sh

    def write_row(self,sh:xl.Sheet,cols:list,bold=False):

        for c in range(len(cols)):

            if isinstance(cols[c],Currency):
                sh.cells[self.row,c].number_format = f'{cols[c].unit}#{"".join(cols[c].mode*[","])}.00 \"{"".join(cols[c].mode*["M"])}\"'

            sh.cells[self.row,c].value = cols[c] if type(cols[c]) == str else float(cols[c])
            sh.cells[self.row,c].font.bold = bold
        self.row += 1


class CapitalCostBuildUp(ReportSection):

    def __init__(self,modules:list[Module],wc:float|None=None):

        self.mods = modules

        self.hxs = [i for i in filter(lambda m: isinstance(m,HeatExchanger),self.mods)]
        self.reacts = [i for i in filter(lambda m: isinstance(m,Reactor),self.mods)]
        self.pumps = [i for i in filter(lambda m: isinstance(m,Pump),self.mods)]
        self.firedHeat = [i for i in filter(lambda m: isinstance(m,FiredHeater),self.mods)]
        self.columns = [i for i in filter(lambda m: isinstance(m,Column),self.mods)]
        self.compressors = [i for i in filter(lambda m: isinstance(m,Compressor),self.mods)]
        self.vessels = [i for i in filter(lambda m: isinstance(m,Vessel),self.mods)]
        self.tanks = [i for i in filter(lambda m: isinstance(m,Tank),self.mods)]

        self.CE = Module.CE
        self.baseCE = Module.baseCE
        self.totBaseCost = sum([m.baseCost for m in self.mods])
        self.totBmCost = sum([m.bmCost for m in self.mods])
        self.totEscBmCost = sum([m.updatedBmCost for m in self.mods])
        self.initCatCost = sum([m.catalyst.value for m in self.reacts])
        self.totEscBaseCost = sum([m.updatedBaseCost for m in self.mods])
        self.instControls = self.totEscBaseCost*0.55
        self.costTBM = self.totEscBmCost+self.initCatCost+self.instControls

        self.sitePrep = self.costTBM*0.05
        self.service = self.costTBM*0.05

        self.steamAmount = sum([m.steamStream.flow for m in self.hxs])
        self.steamCost = 930*self.steamAmount**0.81*self.CE/self.baseCE

        self.twAmount = sum([m.twFlow for m in self.hxs])
        self.twCost = Currency(1100*(self.twAmount/500)**0.68*self.CE/self.baseCE)

        self.elecAmount = sum([m.powerConsumption for m in self.pumps])*0.7457
        self.elecCost = Currency(2900000*(self.elecAmount/1000)**0.83*self.CE/self.baseCE)

        self.costDPI = self.costTBM + self.sitePrep+self.service+self.steamCost+self.twCost+self.elecCost

        self.conting = 0.18*self.costDPI
        self.costTDC = self.costDPI+self.conting

        self.land = self.costTDC*.02
        self.royalties = self.costTDC*.02
        self.startup = self.costTDC*.1

        self.costTPI = self.costTDC+self.land+self.royalties+self.startup

        self.wc = wc if wc else 0.15*self.costTPI
        self.costTCI = self.costTPI+self.wc

    def build_sheet(self,wb:xl.Book,report_title:str):

        sh=super().build_sheet(wb,'Capital Cost IF','CAPITAL COST BUILD UP -- IF',report_title)

        self.row = 4

        #region Module Breakdown

        #region Heat Exchangers
        if len(self.hxs) > 0:
            self.write_row(sh,['HEAT EXCHANGERS'],True)
            self.write_row(sh,['Name','Pressure','Fp','Tube Length','Area','Fl','Base Cost','Fbm','Fd','Fm','BM Cost'],bold=True)

            for hx in self.hxs:
                hx:HeatExchanger
                self.write_row(sh,[hx.name,hx.pres,hx.Fp,hx.tubeLength,hx.area,hx.Fl,
                               hx.baseCost,hx.Fbm,hx.Fd,hx.Fm,hx.bmCost])
            self.row += 1
        #endregion

        #region Pumps
        if len(self.pumps)>0:
            self.write_row(sh,['PUMPS'],True)
            self.write_row(sh,['Name','Flow','Height','S','Cpump','Pt','ηp',
                           'Pb','ηm','Pc','Cmotor','Base Cost','Fbm','Fd',
                           'Fm','Fp','BM Cost'],True)
            for p in self.pumps:
                p:Pump
                self.write_row(sh,[p.name,p.flow,p.height,p.size_fac,p.costPump,p.pumpPower,p.etaP,
                               p.pumpBreak,p.etaM,p.powerConsumption,p.costMotor,p.baseCost,p.Fbm,
                               p.Fd,p.Fm,p.Fp,p.bmCost])
            self.row+=1
        #endregion

        #region Compressors
        if len(self.compressors) > 0:
            self.write_row(sh,['COMPRESSORS'],True)
            self.write_row(sh,['Name','Power','Power Consumption','Base Cost',
                               'Fbm','Fd','Fp','Fm','BM Cost'],True)

            for c in self.compressors:
                c:Compressor
                self.write_row(sh,[c.name,c.Pt,c.Pc,c.baseCost,c.Fbm,c.Fd,c.Fp,c.Fm,c.bmCost])
            self.row += 1
        #endregion

        #region Fired Heaters
        if len(self.firedHeat)>0:
            self.write_row(sh, ['FIRED HEATERS'], True)
            self.write_row(sh, ['Name', 'Pressure', 'Q', 'Base Cost', 'Fbm', 'Fd', 'Fm', 'Fp', 'BM Cost'], True)

            for fh in self.firedHeat:
                fh: FiredHeater
                self.write_row(sh, [fh.name, fh.pres, fh.heatLoad, fh.baseCost, fh.Fbm,fh.Fd, fh.Fm, fh.Fp, fh.bmCost])
            self.row += 1
        #endregion

        #region Columns
        if len(self.columns) > 0:
            self.write_row(sh,['COLUMNS'],True)
            self.write_row(sh,['Name','Diameter','Length','Weight','# of Trays','Tray Spacing','FNT','Cshell',
                               'Cpl','Ctrays','Base Cost','Fbm','Fd','Fm','Fp','Fmt','Fs','Ft','BM Cost'],True)

            for cl in self.columns:
                cl:Column
                self.write_row(sh,[cl.name,cl.diameter,cl.length,cl.weight,cl.nTrays,cl.traySpace,cl.Fnt,cl.Cshell,cl.Cpl,
                                   cl.Ctrays,cl.baseCost,cl.Fbm,cl.Fd,cl.Fm,cl.Fp,cl.Fm_tray,cl.Fs,cl.Ft,cl.bmCost])
            self.row += 1
        #endregion

        #region Vessels
        if len(self.vessels)>0:
            self.write_row(sh,['VESSELS'],True)
            self.write_row(sh,['Name','Diameter','Length','Weight','Cshell','Cpl','Base Cost','Fbm','Fd',
                               'Fm','Fp','BM Cost'])

            for v in self.vessels:
                v:Vessel
                self.write_row(sh,[v.name,v.diameter,v.length,v.weight,v.Cshell,
                               v.Cpl,v.baseCost,v.Fbm,v.Fd,v.Fm,v.Fp,v.bmCost])
            self.row+=1
        #endregion

        #region Tanks
        if len(self.tanks) > 0:
            self.write_row(sh,['TANKS'],True)
            self.write_row(sh,['Name','Flow','Volume','Base Cost','Fbm','Fd','Fm','Fp','BM Cost'],True)

            for t in self.tanks:
                t:Tank
                self.write_row(sh,[t.name,t.flow,t.vol,t.baseCost,t.Fbm,t.Fd,t.Fm,t.Fp,t.bmCost])

        #endregion

        #endregion

        self.row += 4

        #region Summary
        self.write_row(sh,['Summary Table'],True)
        self.write_row(sh,['','Base Cost','Escalated Base Cost','BM Cost','Escalated Bare Module Cost'],True)

        def write_sum_sec(title,module):
            if len(module) == 0: return
            self.write_row(sh,[title],True)
            for m in module:
                self.write_row(sh,[m.name,m.baseCost,m.updatedBaseCost,m.bmCost,m.updatedBmCost])

        write_sum_sec('PUMPS',self.pumps)
        write_sum_sec('COMPRESSORS',self.compressors)
        write_sum_sec('HEAT EXCHANGERS',self.hxs)
        write_sum_sec('FIRED HEATERS',self.firedHeat)
        write_sum_sec('COLUMNS',self.columns)
        write_sum_sec('VESSELS',self.vessels)
        write_sum_sec('TANKS',self.tanks)

        self.write_row(sh,['Total',self.totBaseCost,self.totEscBaseCost,self.totBmCost,self.totEscBmCost],True)

        self.row += 1
        self.write_row(sh,['Total Escalated BM Cost','',self.totEscBmCost],True)
        self.write_row(sh,['Initial Catalyst','',self.initCatCost],True)
        self.write_row(sh,['Instrument and Controls','',self.instControls],True)
        self.write_row(sh,['Total Bare Module Cost','',self.costTBM],True)
        self.write_row(sh,['','Site Prep',self.sitePrep])
        self.write_row(sh,['','Service',self.service])
        self.write_row(sh,['','Steam',self.steamCost])
        self.write_row(sh,['','TW',self.twCost])
        self.write_row(sh,['','Electric',self.elecCost])
        self.write_row(sh,['Direct Permanent Investment','',self.costDPI],True)
        self.write_row(sh,['','Contigency/Contractors',self.conting])
        self.write_row(sh,['Total Depriciable Capital','',self.costTDC],True)
        self.write_row(sh,['','Land',self.land])
        self.write_row(sh,['','Royalties',self.royalties])
        self.write_row(sh,['','Startup',self.startup])
        self.write_row(sh,['Total Permanent Investment','',self.costTPI],True)
        self.write_row(sh,['','Working Capital',self.wc])
        self.write_row(sh,['Total Capital Investment','',self.costTCI],True)

        sh.autofit(axis='columns')

        return sh


class OperatingCosts:

    opHours = 8000
    hourlyWage = Currency(40)
    shifts = 5
    hrsPerShift = 2080
    taxInsRate = 0.02

    def __init__(self,sales:list[RawMaterial]=(),costs:list[RawMaterial]=(),
                 modules:list[Module]=(),TDC=Currency(0),Cp=Currency(0)):

        self.sales = sales
        self.costs = costs
        self.matlCost = sum([m.rate*m.flow*self.opHours for m in self.costs])
        self.mods = modules

        self.pumps = filter(lambda m: isinstance(m,Pump),self.mods)
        self.hxs = filter(lambda m: isinstance(m,HeatExchanger),self.mods)
        self.firedHeaters = filter(lambda m: isinstance(m,FiredHeater),self.mods)
        self.columns = filter(lambda m: isinstance(m,Column),self.mods)
        self.reacts = filter(lambda m: isinstance(m,Reactor),self.mods)

        self.elecAmount = sum([m.powerConsumption for m in self.pumps])

        self.steamLoads = {}
        self.steamCosts = {}

        for hx in self.hxs:
            hx:HeatExchanger

            if hx.steamStream.pres == 0: continue

            try:
                self.steamLoads[hx.steamStream.pres] += hx.steamStream.heatLoad
            except KeyError:
                self.steamLoads[hx.steamStream.pres] = hx.steamStream.heatLoad

            try:
                self.steamCosts[hx.steamStream.pres] += hx.steamStream.cost(self.opHours)
            except KeyError:
                self.steamCosts[hx.steamStream.pres] = hx.steamStream.cost(self.opHours)

        self.twAmount = sum([m.twFlow for m in self.hxs])

        self.ngAmount = sum([m.ngFlow for m in self.hxs])

        self.elecCost = self.elecAmount*0.0711*self.opHours
        self.totalSteamCost = sum(self.steamCosts.values())
        self.twCost = self.twAmount*0.46*self.opHours
        self.ngCost = self.ngAmount*3.63*self.opHours

        self.utilCost = self.elecCost+self.totalSteamCost+self.twCost+self.ngCost

        opPerHx = 0.1
        opPerComp = 0.1
        opPerFiredHeater = 0.3
        opPerColumn = 0.25
        opPerReact = 0.3
        opPerTank =0.1

        nOps = opPerHx*len([m for m in self.hxs])+opPerComp*(0)+opPerFiredHeater*len([m for m in self.firedHeaters])+\
            opPerColumn*len([m for m in self.columns])+opPerReact*len([m for m in self.reacts])+\
               opPerTank*len([m for m in self.reacts])

        self.nOps = int(nOps // 1) + 1 if nOps % 1 != 0 else int(nOps)

        self.DWB = self.nOps*self.hourlyWage*self.shifts*self.hrsPerShift
        self.salaries = self.DWB*0.15
        self.services = self.DWB*0.06
        self.techAssist = 6e4*self.nOps
        self.cntrlLab = 6.5e4*self.nOps

        self.opsCost = self.DWB+self.salaries+self.services+self.techAssist+self.cntrlLab

        self.TDC = TDC
        self.Cp = Cp

        self.mDWB = 0.035*self.TDC
        self.mSalaries = 0.25*self.mDWB
        self.matlService = self.mDWB
        self.mOverhead = .05*self.TDC

        self.maintCost = self.mDWB+self.mSalaries+self.matlService+self.mOverhead

        self.moSWB = self.DWB+self.salaries+self.mDWB+self.mSalaries
        self.genPlantOv = 0.071*self.moSWB
        self.mechService = 0.024*self.moSWB
        self.hr = 0.059*self.moSWB
        self.buisService = 0.074*self.moSWB

        self.opOverheadCost = self.moSWB+self.genPlantOv+self.mechService+self.hr+self.buisService

        self.propTaxIns = self.taxInsRate*self.TDC

        self.depr = (self.TDC-self.Cp/10)/10

        self.salesCost = sum([m.flow*m.rate*self.opHours for m in self.sales])
        self.sellExp = 0.03*self.salesCost
        self.dirResearch = 0.048*self.salesCost
        self.allResearch = 0.005*self.salesCost
        self.adminExp = 0.02*self.salesCost
        self.manIncComp = 0.0125*self.salesCost

        self.genExp = self.sellExp+self.dirResearch+self.allResearch+self.adminExp+self.manIncComp

        self.COM = self.matlCost+self.utilCost+self.opsCost+self.maintCost+self.propTaxIns+self.depr
        self.totalProductionCost = self.COM+self.genExp


class WorkingCapitalBuildUp:

    def __init__(self,COM:Currency,Sales:Currency,FeedCost:Currency):
        self.COM = COM
        self.sales = Sales
        self.feedCost = FeedCost

        self.cashReserves = self.COM/12
        self.inventory = self.sales/365*7
        self.accountsRecievable = self.sales/12
        self.accountsPayable = self.feedCost/12

        self.wc = self.cashReserves+self.inventory+self.accountsRecievable-self.accountsPayable


class ProfitabilityAnalysis:

    taxRate = 0.4
    minROI = 0.22

    def __init__(self,sales:Currency,costs:Currency,Depreciation:Currency,TCI:Currency,TDC:Currency):
        self.sales = sales
        self.costs = costs
        self.depreciation = Depreciation
        self.TCI = TCI
        self.TDC = TDC

        self.ROI = (self.sales-self.costs)*(1-self.taxRate)/self.TCI
        self.paybackPeriod = self.TDC/((1-self.taxRate)*(self.sales-self.costs)+self.depreciation)
        self.ventureProfit = (self.sales-self.costs)*(1-self.taxRate)-self.minROI*self.TCI
        0
