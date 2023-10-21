import xlwings as xl
from Modules import *
from Currency import Currency
from OperatingCosts import OperatingCosts
import datetime


class Report:

    def __init__(self, Report_Name: str = 'ECONOMIC REPORT',Process_Modules:list[Module]=()):

        self.reportName = Report_Name
        self.modules = Process_Modules

        self.wb = xl.Book()

        self.mod_sh = self.__build_modules_sheet()

    def __build_modules_sheet(self):
        sh = self.wb.sheets.add("Modules Costs IF")

        sh.cells[0,0].value = 'CAPITAL COST BUILDUP -- IF METHOD'
        sh.cells[1,0].value = self.reportName.upper()
        sh.cells[2,0].value = datetime.date.today().strftime('%d %B %Y').upper()

        # Row to start listing modules on sheet
        row=4

        #region Heat Exchangers

        hxs = filter(lambda m: isinstance(m,HeatExchanger),self.modules)

        sh.cells[row,0].value = 'HEAT EXCHANGERS'
        row += 1

        cols = ['Name','Pressure (PSIG)','Tube Length (ft)', 'Area (ft^2)','Fbm','Fl','Fp','Fd','Fm','Cbase','Cbm']
        for c in range(len(cols)):
            sh.cells[row,c].value=cols[c]
        row+=1

        for hx in hxs:
            hx:HeatExchanger
            cols = [hx.name,hx.pres,hx.tubeLength,hx.area,hx.Fbm,hx.Fl,hx.Fp,hx.Fd,hx.Fm,hx.baseCost,hx.bmCost]
            for c in range(len(cols)):
                if isinstance(cols[c],Currency):
                    m_string = "".join(cols[c].mode*["\"M\""])
                    sh.cells[row,c].number_format = f'{cols[c].unit}#{"".join(cols[c].mode*[","])}.00 ' \
                                                    f'{m_string}'
                sh.cells[row,c].value = float(cols[c]) if type(cols[c])!=str else cols[c]
            row += 1

        row += 1

        #endregion

        #region Pumps

        pumps = filter(lambda m: isinstance(m,Pump),self.modules)

        cols = ['Name','Q (gpm)','Height (ft)','Pt (HP)','Ft Pump','Ft Motor','S','ηp','ηm']

        #endregion

        return sh


e105 = HeatExchanger('E-105',
                     '',
                     Pressure=554,
                     Tube_Length=20,
                     Area=2250,
                     Matl_A=Material.CarbonSteel,
                     Matl_B=Material.CarbonSteel,
                     Hx_Type=HeatExchangerType.Fixed_Head)

e125 = HeatExchanger('E-125',
                     '',
                     Pressure=474,
                     Tube_Length=20,
                     Area=3798,
                     Matl_A=Material.CarbonSteel,
                     Matl_B=Material.CarbonSteel,
                     Hx_Type=HeatExchangerType.Fixed_Head)

e215 = HeatExchanger('E-215',
                     '',
                     Pressure=1200,
                     Tube_Length=16,
                     Area=618,
                     Matl_A=Material.CarbonSteel,
                     Matl_B=Material.CarbonSteel,
                     Hx_Type=HeatExchangerType.Kettle)

p100 = Pump('P-100',
            '',
            Q=57.7,
            H=1478,
            FT_pump=1.35,
            FT_motor=1.8,
            PT=18.7,
            Matl=Material.CastIron)

test_report = Report(Report_Name='Test economic report',
                     Process_Modules=[e105,e125,e215,p100])