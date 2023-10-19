class Report:

    def __init__(self,Report_Name:str,Report_File_Name:str|None=None):

        if not Report_File_Name: Report_File_Name = f'{Report_Name}.xlsx'

        self.reportName = Report_Name
        self.reportFileName = Report_File_Name
        