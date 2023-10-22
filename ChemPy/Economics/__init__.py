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

    def __build_modules_sheet(self):
        sh = self.wb.sheets.add("Modules Costs IF")

        self.__build_sheet_header(sh,'MODULE COST BREAKDOWN -- IF METHOD')

        # Row to start listing modules on sheet
        row=4

        def write_header(sh:xl.Sheet,cols,row):
            for c in range(len(cols)):
                sh.cells[row, c].value = cols[c]
                sh.cells[row,c].font.bold = True

        def write_row(sh,cols,row):
            for c in range(len(cols)):
                if isinstance(cols[c],Currency):
                    m_string = "".join(cols[c].mode*["\"M\""])
                    sh.cells[row,c].number_format = f'{cols[c].unit}#{"".join(cols[c].mode*[","])}.00 ' \
                                                    f'{m_string}'
                sh.cells[row,c].value = float(cols[c]) if type(cols[c])!=str else cols[c]


        #region Heat Exchangers

        hxs = filter(lambda m: isinstance(m,HeatExchanger),self.modules)

        sh.cells[row,0].value = 'HEAT EXCHANGERS'
        sh.cells[row,0].font.bold=True
        row += 1

        cols = ['Name','Pressure (PSIG)','Tube Length (ft)', 'Area (ft^2)','Fbm','Fl','Fp','Fd','Fm','Cbase','Cbm']

        write_header(sh,cols,row)

        row+=1

        for hx in hxs:
            hx:HeatExchanger
            cols = [hx.name,hx.pres,hx.tubeLength,hx.area,hx.Fbm,hx.Fl,hx.Fp,hx.Fd,hx.Fm,hx.baseCost,hx.bmCost]
            write_row(sh,cols,row)
            row += 1

        row += 1

        #endregion

        #region Pumps

        sh.cells[row,0].value = 'PUMPS'
        sh.cells[row,0].font.bold = True
        row += 1

        pumps = filter(lambda m: isinstance(m,Pump),self.modules)

        cols = ['Name','Flow (gpm)','Height (ft)','Pt (HP)','Ft Pump','Ft Motor','S','ηp','ηm','Pb (HP)','Pc (HP)',
                'Fbm','Fd','Fm','Fp','Cpump','Cmotor','Cpm','Cbm']

        write_header(sh,cols,row)

        row += 1

        for p in pumps:
            p:Pump
            cols = [p.name,p.flow,p.height,p.pumpPower,p.FT_pump,p.FT_motor,p.size_fac,p.etaP,p.etaM,p.pumpBreak,
                    p.powerConsumption,p.Fbm,p.Fd,p.Fm,p.Fp,p.costPump,p.costMotor,p.baseCost,p.bmCost]
            write_row(sh,cols,row)
            row += 1
        row += 1
        #endregion

        #region Columns

        sh.cells[row,0].value = 'COLUMNS'
        sh.cells[row,0].font.bold = True
        row += 1

        columns = filter(lambda m: isinstance(m,Column),self.modules)

        cols = ['Name','Diamter (ft)','Length (ft)','Weight (lbs)','# of Trays','Tray Spacing (in)',
                'Fbm','Fd','Fm','Fp','Fm Trays','Fs','Ft','Fnt','Cshell','Cpl','Ctrays','Base Cost','BM Cost']

        write_header(sh,cols,row)

        row += 1

        for col in columns:
            col:Column
            cols = [col.name,col.diameter,col.length,col.weight,col.nTrays,col.traySpace,col.Fbm,
                    col.Fd,col.Fm,col.Fp,col.Fm_tray,col.Fs,col.Ft,col.Fnt,col.Cshell,col.Cpl,col.Ctrays,
                    col.baseCost,col.bmCost]

            write_row(sh,cols,row)

            row += 1
        row += 1

        #endregion

        #region Vessels

        sh.cells[row,0].value='VESSELS'
        sh.cells[row,0].font.bold=True
        row += 1

        vesls = filter(lambda m: isinstance(m,Vessel),self.modules)

        cols = ['Name','Diameter (ft)','Length (ft)','Weight (lbs)','Fbm','Fd','Fm','Fp','Cshell',
                'Cpl','Cbase','Cbm']
        write_header(sh,cols,row)
        row += 1

        for v in vesls:
            v:Vessel
            cols = [v.name,v.diameter,v.length,v.weight,v.Fbm,v.Fd,v.Fm,v.Fp,v.Cshell,v.Cpl,v.baseCost,
                    v.bmCost]
            write_row(sh,cols,row)
            row += 1
        row += 1

        #endregion

        return sh


Currency.mode = 1

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
            Flow=57.7,
            Height=1478,
            FT_pump=1.35,
            FT_motor=1.8,
            PT=18.7,
            Matl=Material.CastIron)

p140 = Pump('P-140',
            '',
            Flow=97.6,
            Height=27.4,
            FT_pump=1.35,
            FT_motor=1.8,
            PT=0.57)

p260 = Pump('P-260',
            '',
            Flow=22.2,
            Height=1648,
            FT_motor=1.8,
            FT_pump=1.35,
            PT=6.74)

cl200 = Column('CL-200',
               '',
               Diameter=2,
               Length=32,
               Weight=391,
               nTrays=6,
               TrayType=TrayTypes.Sieve,
               TraySpacing=24)

cl220 = Column('CL-220',
               '',
               Diameter=4.5,
               Length=82,
               Weight=9097,
               nTrays=31,
               TrayType=TrayTypes.Sieve,
               TraySpacing=24)

cl240 = Column('CL-240',
               '',
               Diameter=2,
               Length=50,
               Weight=1359,
               nTrays=15,
               TrayType=TrayTypes.Sieve,
               TraySpacing=24)

v130 = Vessel('V-130',
              '',
              Diameter=3.5,
              Length=14,
              Weight=6978,
              Orientation=VesselOrientation.Vert,
              Material=Material.CarbonSteel)

test_report = Report(Report_Name='Test economic report',
                     Process_Modules=[e105,e125,e215,p100,p140,p260,cl200,cl220,cl240,
                                      v130])