class EmergencyPerson:
    def __init__(self, name=None, first_name=None, phone=None, cellphone_format_international=None):
        if name is None:
            self.name = "DESHENG"
            self.first_name = "LI"
            self.phone = "185 1958 2008"
            self.cellphone_format_international = "+86 185 1958 2008"
        else:
            self.name = name
            self.first_name = first_name
            self.phone = phone
            self.cellphone_format_international = cellphone_format_international