class Country:
    country_to_id = {
        "Brasil": 30,
        "Austria": 14,
        "China": 44,
        "Australia": 13,
        "Venezuela": 237,
        "Mexico": 142
    }

    country_to_idalpha3 = {
        "Brasil": "BRA",
        "Austria": "AUT",
        "China": "CHN",
        "Australia": "AUS",
        "Venezuela": "VEN",
        "Mexico": "MEX"
    }

    country_to_idalpha2 = {
        "Brasil": "BR",
        "Austria": "AT",
        "China": "CN",
        "Australia": "AU",
        "Venezuela": "VE",
        "Mexico": "MX"
    }

    def __init__(self, country=None):
        if country is None:
            # Default values (Austria)
            self.country_id = 14
            self.idalpha3 = "AUT"
            self.idalpha2 = "AT"
            self.tiene_edos = 1
            self.id_pais = 14
            self.cad_nombre_es = "Austria"
        else:
            self.country_id = self.country_to_id.get(country)
            self.idalpha3 = self.country_to_idalpha3.get(country)
            self.idalpha2 = self.country_to_idalpha2.get(country)
            self.tiene_edos = 1  # Default value, not set in Java constructor
            self.id_pais = self.country_to_id.get(country)
            self.cad_nombre_es = country