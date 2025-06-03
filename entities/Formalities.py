class Formalities:
    formalititesToId = {
        "Visas": "31"
    }

    typeToId = {
        "Sin permiso del INM": "10",
        "Con permiso del INM (Validación vía servicio web con el INM)": "11"
    }

    subtypeToId = {
        "Visitante sin permiso para realizar actividades remuneradas": "17"
    }

    def __init__(self, formalitites_name=None, formalitites_type_name=None, formalitites_subtype_name=None,
                 passportNumber="", nud=""):
        if formalitites_name is None:
            self.formalitites_id = "31"
            self.formalitites_name = "Visas"
            self.formalitites_type_id = "10"
            self.formalitites_type_name = "Sin permiso del INM"
            self.formalitites_subtype_id = "17"
            self.formalitites_subtype_name = "Visitante sin permiso para realizar actividades remuneradas"
            self.passportNumber = ""
            self.nud = ""
        else:
            self.formalitites_name = formalitites_name
            self.formalitites_id = self.formalititesToId.get(formalitites_name, "")
            self.formalitites_type_name = formalitites_type_name
            self.formalitites_type_id = self.typeToId.get(formalitites_type_name, "")
            self.formalitites_subtype_name = formalitites_subtype_name
            self.formalitites_subtype_id = self.subtypeToId.get(formalitites_subtype_name, "")
            self.passportNumber = passportNumber
            self.nud = nud