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
        self.capitalFormSheet = self.capitalCost.build_sheet_with_formulas(self.wb,'Capital-IF w Formula'
                                                                           ,'CAPITAL COST BUILDUP -- IF',
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

        sh.cells[2,0].value = '\'UPDATED ON '+datetime.date.today().strftime('%d %B %Y').upper()
        sh.cells[2,0].font.bold = True

        return sh

    def write_row(self,sh:xl.Sheet,cols:list,bold:bool|list[bool]=False):

        for c in range(len(cols)):

            if isinstance(cols[c],Currency):
                sh.cells[self.row,c].number_format = f'{cols[c].unit}#{"".join(cols[c].mode*[","])}.00 \"{"".join(cols[c].mode*["M"])}\"'

            sh.cells[self.row,c].value = cols[c] if type(cols[c]) == str else float(cols[c])
            if type(bold) is bool:
                sh.cells[self.row,c].font.bold = bold
            elif type(bold) is list:
                sh.cells[self.row,c].font.bold = bold[c]
        self.row += 1

    def write_row_form(self,sh:xl.Sheet,forms:list,curr_form:list[bool],bold:bool|list[bool]=False):
        for c in range(len(forms)):
            sh.cells[self.row, c].formula = forms[c]
            if type(bold) is bool:
                sh.cells[self.row, c].font.bold = bold
            elif type(bold) is list:
                sh.cells[self.row, c].font.bold = bold[c]
            if curr_form[c]:
                try:
                    mode = int(np.log(float(sh.cells[self.row,c].value))//np.log(1e3))
                except BaseException as err:
                    print(err)
                    print(sh.cells[self.row,c].value)
                    print(forms[c])
                    raise BaseException
                sh.cells[self.row,c].number_format = f'$#{"".join(mode*[","])}.00 \"{"".join(mode*["M"])}\"'
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
        self.tanks = [i for i in filter(lambda m: isinstance(m,Tank),self.mods)]

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
                   Currency(1100*(sum([m.twMassFlow for m in self.hxs])/500)**0.68).update_cost(self.CE,567)),
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
            for p in self.pumps:self.write_row(sh,p.generate_row_xl())
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
            self.row+=1

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
            self.write_row(sh,VerticalVessel.xlHeader,True)
            for vves in self.verticalVessels: self.write_row(sh,vves.generate_row_xl())
            self.row+=1

        if len(self.horizontalVessels)>0:
            self.write_row(sh,['Horizontal Vessels'],True)
            self.write_row(sh,HorizontalVessel.xlHeader,True)
            for hves in self.horizontalVessels: self.write_row(sh,hves.generate_row_xl())
            self.row+=1

        if len(self.tanks)>0:
            self.write_row(sh,['Tanks'],True)
            self.write_row(sh,Tank.xlHeader,True)
            for t in self.tanks: self.write_row(sh,t.generate_row_xl())
            self.row+=1

        self.write_row(sh,['Based on CE Index',self.CE],[True,False])
        self.write_row(sh,['Total Escalated Bare Module Cost',self.totEscBmCost],[True,False])
        self.write_row(sh,['Initial Catalyst',self.catalystCost],[True,False])
        self.write_row(sh,['Instruments and Controls',self.instrumentAndControls],[True,False])
        self.write_row(sh,['Total Bare Module Cost',self.TBM],True)
        self.write_row(sh,['Site Prep',self.sitePrep],[True,False])
        self.write_row(sh,['Service',self.service],[True,False])
        self.write_row(sh,['Steam',self.allocated['Steam'][1]],[True,False])
        self.write_row(sh,['TW',self.allocated['TW'][1]],[True,False])
        self.write_row(sh,['Electricity',self.allocated['Elec'][1]],[True,False])
        self.write_row(sh,['Direct Permanent Investment',self.DPI],True)
        self.write_row(sh,['Land',self.land],[True,False])
        self.write_row(sh,['Royalties',self.royalties],[True,False])
        self.write_row(sh,['Startup',self.startup],[True,False])
        self.write_row(sh,['Total Permanent Investment',self.TPI],True)
        self.write_row(sh,['Working Capital',self.wc],[True,False])
        self.write_row(sh,['Total Capital Investment',self.TCI],True)

        sh.autofit(axis='columns')

        return sh

    def build_sheet_with_formulas(self,wb:xl.Book,sh_name,title,report_title):
        sh=super().build_sheet(wb,sh_name,title,report_title)

        self.row =4

        if len(self.pumps) > 0:
            self.write_row(sh,['PUMPS'],True)
            self.write_row(sh, Pump.xlHeader, True)
            for p in self.pumps:self.write_row_form(sh,*p.generate_formulas_xl(sh,self.row+1))
            self.row+=1

        if len(self.comps) > 0:
            self.write_row(sh,['COMPRESSORS'],True)
            self.write_row(sh,Compressor.xlHeader,True)
            for c in self.comps: self.write_row_form(sh,*c.generate_formulas_xl(sh,self.row+1))
            self.row += 1

        if len(self.hxs)>0:
            self.write_row(sh,['HEAT EXCHANGERS'],True)
            self.write_row(sh,HeatExchanger.xlHeader,True)
            for h in self.hxs: self.write_row_form(sh,*h.generate_formulas_xl(sh,self.row+1))
            self.row+=1

        if len(self.fHeat)>0:
            self.write_row(sh,['FIRED HEATERS'],True)
            self.write_row(sh,FiredHeater.xlHeader,True)
            for f in self.fHeat: self.write_row_form(sh,*f.generate_formulas_xl(sh,self.row+1))
            self.row += 1

        if len(self.columns)>0:
            self.write_row(sh,['COLUMNS'],True)
            self.write_row(sh,Column.xlHeader,True)
            for c in self.columns: self.write_row_form(sh,*c.generate_formulas_xl(sh,self.row+1))
            self.row +=1

        if len(self.verticalVessels)>0:
            self.write_row(sh,['Vertical Vessels'],True)
            self.write_row(sh,VerticalVessel.xlHeader,True)
            for vves in self.verticalVessels: self.write_row_form(sh,*vves.generate_formulas_xl(sh,self.row+1))
            self.row+=1

        if len(self.horizontalVessels)>0:
            self.write_row(sh,['Horizontal Vessels'],True)
            self.write_row(sh,HorizontalVessel.xlHeader,True)
            for hves in self.horizontalVessels: self.write_row_form(sh,*hves.generate_formulas_xl(sh,self.row+1))
            self.row+=1

        if len(self.tanks)>0:
            self.write_row(sh,['Tanks'],True)
            self.write_row(sh,Tank.xlHeader,True)
            for t in self.tanks: self.write_row_form(sh,*t.generate_formulas_xl(sh,self.row+1))
            self.row+=1

        self.row += 4
        self.write_row(sh,['Projected Cost Index','','',self.CE],True)
        sh.range(f'D{self.row}').name = 'CE'
        self.row+=1
        self.write_row(sh,['','Correlation Cost (CE=567)','=TEXTJOIN(" ",TRUE,"Escalated Cost (CE=",CE,")")'],True)
        self.write_row_form(sh,['Cp',f'={"+".join([f"CP_{a.xlNameRange}" for a in self.mods])}',f'=b{self.row+1}*CE/567'],
                            [False,True,True],[True,False,True])
        sh.range(f'c{self.row}').name = 'Cp'
        self.write_row_form(sh,['Cbm',f'={"+".join([f"BM_{a.xlNameRange}" for a in self.mods])}',f'=b{self.row+1}*CE/567'],
                            [False,True,True],[True,False,True])
        sh.range(f'c{self.row}').name = 'Cbm'
        self.row+=1
        self.write_row(sh,['','Mass','Rate','Cost'],True)
        self.reactors:list[VerticalReactor | HorizontalReactor]
        if len(self.reactors)>0:
            start_row = self.row+1
            for cat in [r.catalyst for r in self.reactors]:
                self.write_row_form(sh,[cat.name,cat.amount,cat.rate,f'=b{self.row+1}*c{self.row+1}'],[False,False,True,True])
            end_row = self.row
            self.write_row_form(sh,['','','Total Initial Catalyst Cost',f'=SUM(d{start_row}:d{end_row})'],
                                [False,False,False,True],True)
        else:
            self.write_row(sh,['Initial Catalyst Cost','','',Currency(0)],True)
        sh.range(f'd{self.row}').name = 'Ccat'
        self.row += 1
        self.write_row_form(sh,['Instruments and Controls','55%','Cp',f'=b{self.row+1}*Cp'],[False,False,False,True])
        sh.range(f'd{self.row}').name = 'InstControls'
        self.write_row_form(sh,['Total Bare Module Cost','','','=Cbm+Ccat+InstControls'],[False,False,False,True],True)
        sh.range(f'd{self.row}').name = 'TBM'




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



