from ChemPy.Economics.Currency import Currency

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


class SteamStream:

    pres_dict = {
        1200:11.02,
        600:8.91,
        300:7.81,
        150:7.10,
        90:6.7,
        30:6.07
    }

    def __init__(self,pressure,flow,heat_load):
        self.pres = pressure
        self.flow = flow
        self.heatLoad = heat_load

    def cost(self,hours):
        return hours*self.flow*self.pres_dict[self.pres]


class RawMaterial:

    def __init__(self,name,cost_per_pound:Currency,flow):

        self.name = name
        self.rate = cost_per_pound
        self.flow = flow
        self.value = self.rate*self.flow


class Catalyst(RawMaterial):

    def __init__(self,name,volume,density,price_per_pound):

        super().__init__(name,price_per_pound,volume*density)