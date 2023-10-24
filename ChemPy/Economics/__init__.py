import xlwings as xl
from ChemPy.Economics.Modules import *
from ChemPy.Economics.Materials import *
from ChemPy.Economics.Currency import Currency
import datetime


class Report:

    def __init__(self, Report_Name: str = 'ECONOMIC REPORT',Process_Modules:list[Module]=(),
                 sales:list[RawMaterial]=(),costs:list[RawMaterial]=()):

        self.reportName = Report_Name
        self.modules = Process_Modules

        self.wb = xl.Book()

        self.capitalCost = CapitalCostBuildUp(self.modules)
        self.capitalCostSheet = self.capitalCost.build_sheet(self.wb,'Capital-IF','CAPITAL COST BUILDUP -- IF',
                                                             self.reportName)

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

        sh.cells[2,0].value = '\'UPDATED ON '+datetime.date.today().strftime('%d %B %Y')
        sh.cells[2,0].font.bold = True

        return sh

    def write_row(self,sh:xl.Sheet,cols:list,bold:bool|list=False):

        for c in range(len(cols)):

            if isinstance(cols[c],Currency):
                sh.cells[self.row,c].number_format = f'{cols[c].unit}#{"".join(cols[c].mode*[","])}.00 \"{"".join(cols[c].mode*["M"])}\"'

            sh.cells[self.row,c].value = cols[c] if type(cols[c]) == str else float(cols[c])
            if type(bold) is bool:
                sh.cells[self.row,c].font.bold = bold
            elif type(bold) is list:
                sh.cells[self.row,c].font.bold = bold[c]
        self.row += 1

    def write_row_form(self,sh:xl.Sheet,forms:list,bold=False):
        for c in range(len(forms)):
            sh.cells[self.row, c].formula = forms[c]
            sh.cells[self.row, c].font.bold = bold
        self.row += 1


class CapitalCostBuildUp(ReportSection):

    def __init__(self,modules:list[Module],CE=800,wc=None,):

        self.mods = modules

        self.pumps = [i for i in filter(lambda m: isinstance(m, Pump), self.mods)]
        self.comps = [i for i in filter(lambda m: isinstance(m,Compressor),self.mods)]
        self.hxs = [i for i in filter(lambda m: isinstance(m,HeatExchanger),self.mods)]
        self.fHeat = [i for i in filter(lambda m: isinstance(m,FiredHeater),self.mods)]
        self.columns = [i for i in filter(lambda m: isinstance(m,Column),self.mods)]
        self.verticalVessels = [i for i in filter(lambda m: isinstance(m,VerticalVessel),self.mods)]
        self.horizontalVessels = [i for i in filter(lambda m: isinstance(m,HorizontalVessel),self.mods)]
        self.reactors = [i for i in filter(lambda m: isinstance(m,(HorizontalReactor,VerticalReactor)),self.mods)]

        self.CE = CE
        self.totPurchCost = sum([m.purchCost for m in self.mods])
        self.totEscPurchCost = sum([m.purchCost.update_cost(CE,m.corrCE) for m in self.mods])
        self.totBmCost = sum([m.bmCost for m in self.mods])
        self.totEscBmCost = sum([m.bmCost.update_cost(CE,m.corrCE) for m in self.mods])

        self.reactors:list[VerticalReactor | HorizontalReactor]
        self.catalystCost = sum([m.catalyst.cost for m in self.reactors])
        self.instrumentAndControls = 0.55*self.totEscPurchCost
        self.TBM = self.totEscBmCost+self.catalystCost+self.instrumentAndControls

        self.sitePrep = self.service = 0.05*self.TBM

        self.hxs: list[HeatExchanger]
        self.pumps: list[Pump]
        self.comps: list[Compressor]
        self.allocated = {
            'Steam': (sum([m.steamStream.flow for m in self.hxs]),
                      Currency(930*sum([m.steamStream.flow for m in self.hxs])**0.81).update_cost(self.CE,567)),
            'TW': (sum([m.twMassFlow for m in self.hxs]),
                   Currency(1100*(sum([m.twMassFlow] for m in self.hxs)/500)**0.68).update_cost(self.CE,567)),
            'Elec': (sum([m.Pc for m in self.pumps])+sum([m.Pc for m in self.comps]),
                     Currency(2900000*((sum([m.Pc for m in self.pumps])+sum([m.Pc for m in self.comps])/1000)**0.83)).update_cost(self.CE,567))
        }

        self. DPI = self.TBM + self.sitePrep+self.service+sum([self.allocated[key][1] for key in self.allocated])

        self.contingencyFee = 0.15*self.DPI
        self.contractorsFee = 0.03*self.DPI

        self.TDC = self.DPI + self.contingencyFee+self.contractorsFee

        self.land = self.royalties = 0.02*self.TDC
        self.startup = 0.1*self.TDC

        self.TPI = self.land+self.royalties+self.startup

        self.wc = wc if wc else 0.15*self.TPI

        self.TCI = self.TPI+self.wc

    def build_sheet(self,wb:xl.Book,sh_name,title,report_title):
        sh = super().build_sheet(wb,sh_name,title,report_title)

        self.row = 4

        if len(self.pumps) > 0:
            self.write_row(sh,['PUMPS'],True)
            self.write_row(sh, Pump.xlHeader, True)
            for p in self.pumps: self.write_row(sh,p.generate_row_xl())
            self.row+=1

        if len(self.comps) > 0:
            self.write_row(sh,['COMPRESSORS'],True)
            self.write_row(sh,Compressor.xlHeader,True)
            for c in self.comps: self.write_row(sh,c.generate_row_xl())
            self.row += 1

        if len(self.hxs)>0:
            self.write_row(sh,['HEAT EXCHANGERS'],True)
            self.write_row(sh,HeatExchanger.xlHeader,True)
            for h in self.hxs: self.write_row(sh,h.generate_row_xl())

        if len(self.fHeat)>0:
            self.write_row(sh,['FIRED HEATERS'],True)
            self.write_row(sh,FiredHeater.xlHeader,True)
            for f in self.fHeat: self.write_row(sh,f.generate_row_xl())
            self.row += 1

        if len(self.columns)>0:
            self.write_row(sh,['COLUMNS'],True)
            self.write_row(sh,Column.xlHeader,True)
            for c in self.columns: self.write_row(sh,c.generate_row_xl())
            self.row +=1

        if len(self.verticalVessels)>0:
            self.write_row(sh,['Vertical Vessels'],True)
            self.write_row(sh,[VerticalVessel.xlHeader],True)
            for vves in self.verticalVessels: self.write_row(sh,vves.generate_row_xl())
            self.row+=1

        if len(self.horizontalVessels)>0:
            self.write_row(sh,['Horizontal Vessels'],True)
            self.write_row(sh,[HorizontalVessel.xlHeader],True)
            for hves in self.horizontalVessels: self.write_row(sh,hves.generate_row_xl())
            self.row+=1

        return sh


class OperatingCosts(ReportSection):

    opHour = 8000

    def __init__(self,sales:list[RawMaterial],costs:list[RawMaterial],mods:list[Module]):

        self.saleMatls = sales
        self.costMatls = costs
        self.mods = mods

        self.reacts = [i for i in filter(lambda m: isinstance(m,(HorizontalReactor,VerticalReactor)),self.mods)]
        self.reacts: list[HorizontalReactor | VerticalReactor]

        self.saleValue = sum([m.h_cost(self.opHour) for m in self.saleMatls])
        self.costValue = sum([m.h_cost(self.opHour) for m in self.costMatls])+sum([m.catalyst.cost for m in self.reacts])

        self.pumpsComps = [i for i in filter(lambda m: isinstance(m,(Pump,Compressor)),self.mods)]
        self.pumpsComps: list[Pump | Compressor]
        self.totElec = sum([m.Pc for m in self.pumpsComps])

        self.hxs = [i for i in filter(lambda m: isinstance(m,HeatExchanger),self.mods)]
        self.hxs: list[HeatExchanger]
        self.totTW = sum([m.twVolFlow for m in self.hxs])
        self.totSteam = {}
        for h in self.hxs:
            try:
                self.totSteam[h.steamStream.pres] += h.steamStream.flow
            except KeyError:
                self.totSteam[h.steamStream.pres] = h.steamStream.flow

        self.fHeat = [i for i in filter(lambda m: isinstance(m,FiredHeater),self.mods)]
        self.fHeat:list[FiredHeater]
        self.totNG = sum([m.ngFlow for m in self.fHeat])

        self.elecCost = self.totElec*self.opHour*Currency(0.0711)
        self.twCost = self.totTW*self.opHour*Currency(0.46)/1000
        self.ngCost = self.totNG*Currency(3.63)*self.opHour

        self.nComps = len([i for i in filter(lambda m: isinstance(m,Compressor),self.mods)])
        self.nHxs = len(self.hxs)
        self.nFireHeat = len(self.fHeat)
        self.nTowers = len([i for i in filter(lambda m: isinstance(m,Column),self.mods)])
        self.nReactors = len(self.reacts)

        self.nOperators = 0.1*self.nComps+0.1*self.nHxs+0.3*self.nFireHeat+0.25*self.nTowers+0.3*self.nReactors



