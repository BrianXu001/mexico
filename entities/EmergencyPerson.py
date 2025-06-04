class EmergencyPerson:
    def __init__(self, name=None, firstName=None, phone=None, cellPhoneFormatInternational=None):
        if name is None:
            self.name = "DESHENG"
            self.firstName = "LI"
            self.phone = "185 1958 2008"
            self.cellPhoneFormatInternational = "+86 185 1958 2008"
        else:
            self.name = name
            self.firstName = firstName
            self.phone = phone
            self.cellPhoneFormatInternational = cellPhoneFormatInternational