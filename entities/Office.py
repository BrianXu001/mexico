class Office:
    office_to_id = {
        "BRASILIA": 67,
        "RIO DE JANEIRO": 144,
        "CANBERRA": 74,
        "AUSTRIA": 223,
        "SHANGHAI": 164,
        "GUANGZHOU": 246,
        "BEIJING": 59
    }

    office_to_state = {
        "BRASILIA": "Distrito Federal",
        "RIO DE JANEIRO": "RIO DE JANEIRO",
        "CANBERRA": "AUSTRALIAN CAPITAL TERRITORY",
        "AUSTRIA": "WIEN",
        "SHANGHAI": "SHANGHAI",
        "GUANGZHOU": "GUANGZHOU",
        "BEIJING": "BEIJING"
    }

    office_to_state_id = {
        "BRASILIA": 330029,
        "RIO DE JANEIRO": 330041,
        "CANBERRA": 3358,
        "AUSTRIA": 3380,
        "SHANGHAI": 3667,
        "GUANGZHOU": 329198,
        "BEIJING": 3643
    }

    office_to_longitud = {
        "BRASILIA": -47.883199,
        "RIO DE JANEIRO": -43.174081,
        "CANBERRA": 149.1143319,
        "AUSTRIA": 16.3668846266,
        "SHANGHAI": 121.394374,
        "GUANGZHOU": 113.323205,
        "BEIJING": 116.458656
    }

    office_to_latitud = {
        "BRASILIA": -15.815721,
        "RIO DE JANEIRO": -22.964465,
        "CANBERRA": -35.3040023,
        "AUSTRIA": 48.2127274675,
        "SHANGHAI": 31.180032,
        "GUANGZHOU": 23.132773,
        "BEIJING": 39.944392
    }

    office_to_calle = {
        "BRASILIA": "Av. das Nacóes",
        "RIO DE JANEIRO": "Edificio ABC - Av. Atlântica, 5o andar",
        "CANBERRA": "Perth Avenue",
        "AUSTRIA": "RENNGASSE 5, TOP 6, 1010, WIEN                                                                          ",
        "SHANGHAI": "Dawning Center, Hongbaoshi Rd. 500",
        "GUANGZHOU": "Tianhe Road, Teem Tower Unit 01",
        "BEIJING": "San Li Tun Dong Wu Jie"
    }

    office_to_telefono = {
        "BRASILIA": "55-613204-5200",
        "RIO DE JANEIRO": "-55213262-3200",
        "CANBERRA": "-6126273-3963",
        "AUSTRIA": "00431310738335",
        "SHANGHAI": "-86216125 0220",
        "GUANGZHOU": "-86202208 1540",
        "BEIJING": "-8610 6532-2070"
    }

    def __init__(self, office_name=None):
        if office_name is None:
            self.cat_office_id = 223
            self.var_cad_num_interior = ""
            self.var_id_entidad_federativa = 3380
            self.var_cad_localidad = None
            self.var_id_oficina = 223
            self.var_cad_codigo_postal = ""
            self.var_cad_oficina = "AUSTRIA"
            self.var_cad_correo_electronico = None
            self.var_id_municipio_alcaldia = None
            self.var_num_longitud = 16.3668846266
            self.var_cad_municipio_alcaldia = ""
            self.var_cad_calle = "RENNGASSE 5, TOP 6, 1010, WIEN                                                                          "
            self.var_cad_entidad_federativa = "WIEN"
            self.var_id_localidad = None
            self.var_id_codigo_postal = None
            self.var_cad_num_exterior = ""
            self.var_cad_colonia = ""
            self.is_ome = False
            self.var_cad_num_telefono = "00431310738335"
            self.var_num_latitud = 48.2127274675
        else:
            self.cat_office_id = self.office_to_id.get(office_name)
            self.var_id_entidad_federativa = self.office_to_state_id.get(office_name)
            self.var_id_oficina = self.office_to_id.get(office_name)
            self.var_cad_oficina = office_name
            self.var_num_longitud = self.office_to_longitud.get(office_name)
            self.var_cad_calle = self.office_to_calle.get(office_name)
            self.var_cad_entidad_federativa = self.office_to_state.get(office_name)
            self.var_cad_num_telefono = self.office_to_telefono.get(office_name)
            self.var_num_latitud = self.office_to_latitud.get(office_name)
            # Set default values for other attributes
            self.var_cad_num_interior = ""
            self.var_cad_localidad = None
            self.var_cad_codigo_postal = ""
            self.var_cad_correo_electronico = None
            self.var_id_municipio_alcaldia = None
            self.var_cad_municipio_alcaldia = ""
            self.var_id_localidad = None
            self.var_id_codigo_postal = None
            self.var_cad_num_exterior = ""
            self.var_cad_colonia = ""
            self.is_ome = False