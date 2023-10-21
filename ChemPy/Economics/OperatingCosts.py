from Currency import Currency

class OperatingCosts:
    pass


class ProcMaterial:

    def __init__(self, material_name:str, price_per_pound:Currency):
        self.name = material_name
        self.pplbs = price_per_pound
