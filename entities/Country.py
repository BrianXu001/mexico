class Country:
    countryToId = {
        "Brasil": 30,
        "Austria": 14,
        "China": 44,
        "Australia": 13,
        "Venezuela": 237,
        "Mexico": 142
    }

    countryToIdalpha3 = {
        "Brasil": "BRA",
        "Austria": "AUT",
        "China": "CHN",
        "Australia": "AUS",
        "Venezuela": "VEN",
        "Mexico": "MEX"
    }

    countryToIdalpha2 = {
        "Brasil": "BR",
        "Austria": "AT",
        "China": "CN",
        "Australia": "AU",
        "Venezuela": "VE",
        "Mexico": "MX"
    }

    def __init__(self, country=None):
        if country is None:
            self.country_id = 14
            self.idalpha3 = "AUT"
            self.idalpha2 = "AT"
            self.tiene_edos = 1
            self.id_pais = 14
            self.cad_nombre_es = "Austria"
        else:
            self.country_id = self.countryToId.get(country)
            self.idalpha3 = self.countryToIdalpha3.get(country)
            self.idalpha2 = self.countryToIdalpha2.get(country)
            self.tiene_edos = 1
            self.id_pais = self.countryToId.get(country)
            self.cad_nombre_es = country