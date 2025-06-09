from entities.Country import Country
from entities.State import State
from entities.Office import Office
from entities.Formalities import Formalities
from entities.EmergencyPerson import EmergencyPerson
import json
from datetime import datetime


class Person:
    def __init__(self, *args):
        if len(args) == 0:
            self._init_default()
        elif len(args) == 1 and isinstance(args[0], dict):
            self._init_from_json(args[0])
        elif len(args) == 1 and isinstance(args[0], int):
            self._init_from_office_id(args[0])
        elif len(args) == 2:
            self._init_from_state_and_formalities(args[0], args[1])
        else:
            print("Can not construct class Person!")

    def _init_default(self):
        dst_country = "China"
        dst_state = "Shanghai"
        dst_office = "SHANGHAI"
        nationality = "China"
        country_of_birth = "China"
        state_of_birth = "Beijing"
        from_country = "China"
        from_state = "Beijing"
        formalitites_name = "Visas"
        formalitites_type_name = "Sin permiso del INM"
        formalitites_subtype_name = "Visitante sin permiso para realizar actividades remuneradas"
        passport_number = ""
        nud = ""
        full_name = "JAMES XU"
        name = "JAMES"
        first_name = "XU"
        birthdate = "1993-09-12"
        age = self._calculate_age(birthdate)
        civil_state = 1
        cat_gender_id = 2
        direction = "CHAOYANG JIUXIANQIAO"
        emergency_name = "XIAOSONG"
        emergency_first_name = "XU"
        emergency_phone = "185 1958 2008"
        emergency_cellphone_format_international = "+86 185 1958 2008"

        self.dst_country = Country(dst_country)
        self.dst_state = State(dst_state)
        self.dst_office = Office(dst_office)
        self.nationality = nationality
        self.country_of_birth = country_of_birth
        self.state_of_birth = state_of_birth
        self.from_country = Country(from_country)
        self.from_state = State(from_state)
        self.formalities = Formalities(formalitites_name, formalitites_type_name, formalitites_subtype_name, passport_number, nud)
        self.full_name = full_name
        self.name = name
        self.first_name = first_name
        self.birthdate = birthdate
        self.age = age
        self.civil_state = civil_state
        self.cat_gender_id = cat_gender_id
        self.direction = direction
        self.emergency_person = EmergencyPerson(emergency_name, emergency_first_name, emergency_phone,
                                               emergency_cellphone_format_international)

    def _init_from_state_and_formalities(self, state, formalitites_type):
        print("_init_from_state_and_formalities")
        state_lower = state.lower()
        if state_lower == "shanghai":
            self.dst_state = State("Shanghai")
            self.dst_office = Office("SHANGHAI")
            self.from_state = State("Shanghai")
        elif state_lower == "guangzhou":
            self.dst_state = State("Guangzhou")
            self.dst_office = Office("GUANGZHOU")
            self.from_state = State("Guangzhou")
        elif state_lower == "beijing":
            self.dst_state = State("Beijing")
            self.dst_office = Office("BEIJING")
            self.from_state = State("Beijing")
        else:
            print(state)
            print("Please input right state(shanghai/guangzhou/beijing)!")
            exit(1)

        formalitites_type_lower = formalitites_type.lower()
        if formalitites_type_lower == "sin":
            self.formalities = Formalities("Visas", "Sin permiso del INM",
                                           "Visitante sin permiso para realizar actividades remuneradas", "EJ9023801",
                                           "")
        elif formalitites_type_lower == "con":
            self.formalities = Formalities("Visas", "Con permiso del INM (Validación vía servicio web con el INM)", "",
                                           "EJ9023801", "6288241")
        else:
            print("Please input right formalitites_type(sin/con)!")
            exit(1)

        self.dst_country = Country("China")
        self.nationality = "China"
        self.country_of_birth = "China"
        self.state_of_birth = "Beijing"
        self.from_country = Country("China")
        self.full_name = "JAMES XU"
        self.name = "JAMES"
        self.first_name = "XU"
        self.birthdate = "1993-09-12"
        self.age = self._calculate_age(self.birthdate)
        self.civil_state = 1
        self.cat_gender_id = 2
        self.direction = "CHAOYANG JIUXIANQIAO"
        self.emergency_person = EmergencyPerson("XIAOKAI", "XU", "185 1958 2008", "+86 185 1958 2008")

    def _init_from_json(self, person_json):
        print("_init_from_json")
        self.dst_country = Country(person_json.get("dstCountry"))
        self.dst_state = State(person_json.get("dstState"))
        self.dst_office = Office(person_json.get("dstOffice"))
        self.nationality = person_json.get("nationality")
        self.country_of_birth = person_json.get("countryOfBirth")
        self.state_of_birth = person_json.get("stateOfBirth")
        self.municipality_of_birth = person_json.get("municipalityOfBirth", "")

        self.from_country = Country(person_json.get("fromCountry"))
        self.from_state = State(person_json.get("fromState"))
        formalitites_name = person_json.get("formalitites_name")
        formalitites_type_name = person_json.get("formalitites_type_name")
        formalitites_subtype_name = person_json.get("formalitites_subtype_name", "")
        passport_number = person_json.get("passport", "") if "passport" in person_json else ""
        nud = person_json.get("nut", "") if "nut" in person_json else ""
        self.formalities = Formalities(formalitites_name, formalitites_type_name, formalitites_subtype_name,
                                       passport_number, nud)
        self.name = person_json.get("name")
        self.first_name = person_json.get("firstName")
        self.full_name = f"{self.name} {self.firstName} "
        self.birthdate = person_json.get("birthdate")
        self.age = self._calculate_age(self.birthdate)
        self.civil_state = person_json.get("civilState")
        self.cat_gender_id = person_json.get("cat_gender_id")
        self.direction = person_json.get("fromDirection", "").upper()

        emergency_name = person_json.get("emergencyName")
        emergency_first_name = person_json.get("emergencyFirstName")
        emergency_phone = person_json.get("emergencyPhone")
        emergency_cellphone_format_international = f"+86 {emergency_phone}"
        self.emergencyPerson = EmergencyPerson(emergency_name, emergency_first_name, emergency_phone,
                                               emergency_cellphone_format_international)

        self.start_time = person_json.get("start_time", "0000-00-00")
        self.start_time = "0000-00-00" if not self.start_time else self.start_time
        self.end_time = person_json.get("end_time", "9999-99-99")
        self.end_time = "9999-99-99" if not self.end_time else self.end_time

        self.identification = person_json.get("identification")
        self.id_begin_date = person_json.get("id_begin_date")
        self.id_end_date = person_json.get("id_end_date")

    def _calculate_age(self, birthdate):
        if not birthdate:
            return 0
        birth_date = datetime.strptime(birthdate, "%Y-%m-%d").date()
        today = datetime.today().date()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age

    def _init_from_office_id(self, office_id: int):
        # # GUANGZHOU:246, BEIJING: 59, AUSTRIA:223, CANBERRA:74, RIO DE JANEIRO: 144, SHANGHAI: 164,
        print("__init_from_office_id")
        if office_id == 246:
            self.dstS_state = State("Guangzhou")
            self.dst_office = Office("GUANGZHOU")
            self.dst_country = Country("China")
        elif office_id == 59:
            self.dst_state = State("Beijing")
            self.dst_office = Office("BEIJING")
            self.dst_country = Country("China")
        elif office_id == 164:
            self.dst_state = State("Shanghai")
            self.dst_office = Office("SHANGHAI")
            self.dst_country = Country("China")
        elif office_id == 223:
            self.dst_state = State("Wien")
            self.dst_office = Office("AUSTRIA")
            self.dst_country = Country("Austria")
        elif office_id == 74:
            self.dst_state = State("Australian Capital Territory")
            self.dst_office = Office("CANBERRA")
            self.dst_country = Country("Australia")
        elif office_id == 144:
            self.dst_state = State("Rio de Janeiro")
            self.dst_office = Office("RIO DE JANEIRO")
            self.dst_country = Country("Brasil")
        else:
            print("can not find office_id:", office_id)
            raise Exception("can not find office_id")

        # self.formalities = Formalities("Visas", "Sin permiso del INM", "Visitante sin permiso para realizar actividades remuneradas", "EJ9023801","")
        self.formalities = Formalities("Visas", "Con permiso del INM (Validación vía servicio web con el INM)", "", "EJ9023801", "6288241")

        self.nationality = "China"
        self.country_of_birth = "China"
        self.state_of_birth = "Guangzhou"
        self.from_country = Country("China")
        self.from_state = State("Guangzhou")
        self.full_name = "JAMES LI"
        self.name = "JAMES"
        self.first_name = "LI"
        self.birthdate = "1993-09-12"
        self.age = self._calculate_age(self.birthdate)
        self.civil_state = 1  # 婚姻状态 1:未婚, 2:已婚
        self.cat_gender_id = 2  # 性别 1:女性, 2:男性
        self.direction = "GUANGDONG GUANGZHOU BAIYUN"
        self.emergency_person = EmergencyPerson("YINAN", "LI", "185 1958 2008", "+86 185 1958 2008")