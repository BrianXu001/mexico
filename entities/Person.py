from ..entities.Country import Country
from ..entities.State import State
from ..entities.Office import Office
from ..entities.Formalities import Formalities
from ..entities.EmergencyPerson import EmergencyPerson
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
        dstCountry = "China"
        dstState = "Shanghai"
        dstOffice = "SHANGHAI"
        nationality = "China"
        countryOfBirth = "China"
        stateOfBirth = "Beijing"
        fromCountry = "China"
        fromState = "Beijing"
        formalitites_name = "Visas"
        formalitites_type_name = "Sin permiso del INM"
        formalitites_subtype_name = "Visitante sin permiso para realizar actividades remuneradas"
        passportNumber = ""
        nud = ""
        fullName = "JAMES XU"
        name = "JAMES"
        firstName = "XU"
        birthdate = "1993-09-12"
        age = self._calculate_age(birthdate)
        civilState = 1
        cat_gender_id = 2
        direction = "CHAOYANG JIUXIANQIAO"
        emergencyName = "XIAOSONG"
        emergencyFirstName = "XU"
        emergencyPhone = "185 1958 2008"
        emergencyCellPhoneFormatInternational = "+86 185 1958 2008"

        self.dstCountry = Country(dstCountry)
        self.dstState = State(dstState)
        self.dstOffice = Office(dstOffice)
        self.nationality = nationality
        self.countryOfBirth = countryOfBirth
        self.stateOfBirth = stateOfBirth
        self.fromCountry = Country(fromCountry)
        self.fromState = State(fromState)
        self.formalities = Formalities(formalitites_name, formalitites_type_name, formalitites_subtype_name,
                                       passportNumber, nud)
        self.fullName = fullName
        self.name = name
        self.firstName = firstName
        self.birthdate = birthdate
        self.age = age
        self.civilState = civilState
        self.cat_gender_id = cat_gender_id
        self.direction = direction
        self.emergencyPerson = EmergencyPerson(emergencyName, emergencyFirstName, emergencyPhone,
                                               emergencyCellPhoneFormatInternational)

    def _init_from_state_and_formalities(self, state, formalitites_type):
        state_lower = state.lower()
        if state_lower == "shanghai":
            self.dstState = State("Shanghai")
            self.dstOffice = Office("SHANGHAI")
            self.fromState = State("Shanghai")
        elif state_lower == "guangzhou":
            self.dstState = State("Guangzhou")
            self.dstOffice = Office("GUANGZHOU")
            self.fromState = State("Guangzhou")
        elif state_lower == "beijing":
            self.dstState = State("Beijing")
            self.dstOffice = Office("BEIJING")
            self.fromState = State("Beijing")
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

        self.dstCountry = Country("China")
        self.nationality = "China"
        self.countryOfBirth = "China"
        self.stateOfBirth = "Beijing"
        self.fromCountry = Country("China")
        self.fullName = "JAMES XU"
        self.name = "JAMES"
        self.firstName = "XU"
        self.birthdate = "1993-09-12"
        self.age = self._calculate_age(self.birthdate)
        self.civilState = 1
        self.cat_gender_id = 2
        self.direction = "CHAOYANG JIUXIANQIAO"
        self.emergencyPerson = EmergencyPerson("XIAOKAI", "XU", "185 1958 2008", "+86 185 1958 2008")

    def _init_from_json(self, person_json):
        self.dstCountry = Country(person_json.get("dstCountry"))
        self.dstState = State(person_json.get("dstState"))
        self.dstOffice = Office(person_json.get("dstOffice"))
        self.nationality = person_json.get("nationality")
        self.countryOfBirth = person_json.get("countryOfBirth")
        self.stateOfBirth = person_json.get("stateOfBirth")
        self.municipalityOfBirth = person_json.get("municipalityOfBirth", "")

        self.fromCountry = Country(person_json.get("fromCountry"))
        self.fromState = State(person_json.get("fromState"))
        formalitites_name = person_json.get("formalitites_name")
        formalitites_type_name = person_json.get("formalitites_type_name")
        formalitites_subtype_name = person_json.get("formalitites_subtype_name", "")
        passportNumber = person_json.get("passport", "") if "passport" in person_json else ""
        nud = person_json.get("nut", "") if "nut" in person_json else ""
        self.formalities = Formalities(formalitites_name, formalitites_type_name, formalitites_subtype_name,
                                       passportNumber, nud)
        self.name = person_json.get("name")
        self.firstName = person_json.get("firstName")
        self.fullName = f"{self.name} {self.firstName} "
        self.birthdate = person_json.get("birthdate")
        self.age = self._calculate_age(self.birthdate)
        self.civilState = person_json.get("civilState")
        self.cat_gender_id = person_json.get("cat_gender_id")
        self.direction = person_json.get("fromDirection", "").upper()

        emergencyName = person_json.get("emergencyName")
        emergencyFirstName = person_json.get("emergencyFirstName")
        emergencyPhone = person_json.get("emergencyPhone")
        emergencyCellPhoneFormatInternational = f"+86 {emergencyPhone}"
        self.emergencyPerson = EmergencyPerson(emergencyName, emergencyFirstName, emergencyPhone,
                                               emergencyCellPhoneFormatInternational)

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
        if office_id == 246:
            self.dstState = State("Guangzhou")
            self.dstOffice = Office("GUANGZHOU")
            self.dstCountry = Country("China")
        elif office_id == 59:
            self.dstState = State("Beijing")
            self.dstOffice = Office("BEIJING")
            self.dstCountry = Country("China")
        elif office_id == 164:
            self.dstState = State("Shanghai")
            self.dstOffice = Office("SHANGHAI")
            self.dstCountry = Country("China")
        elif office_id == 223:
            self.dstState = State("Wien")
            self.dstOffice = Office("AUSTRIA")
            self.dstCountry = Country("Austria")
        elif office_id == 74:
            self.dstState = State("Australian Capital Territory")
            self.dstOffice = Office("CANBERRA")
            self.dstCountry = Country("Australia")
        elif office_id == 144:
            self.dstState = State("Rio de Janeiro")
            self.dstOffice = Office("RIO DE JANEIRO")
            self.dstCountry = Country("Brasil")
        else:
            print("can not find office_id:", office_id)
            raise Exception("can not find office_id")

        # self.formalities = Formalities("Visas", "Sin permiso del INM", "Visitante sin permiso para realizar actividades remuneradas", "EJ9023801","")
        self.formalities = Formalities("Visas", "Con permiso del INM (Validación vía servicio web con el INM)", "", "EJ9023801", "6288241")

        self.nationality = "China"
        self.countryOfBirth = "China"
        self.stateOfBirth = "Guangzhou"
        self.fromCountry = Country("China")
        self.fromState = State("Guangzhou")
        self.fullName = "JAMES LI"
        self.name = "JAMES"
        self.firstName = "LI"
        self.birthdate = "1993-09-12"
        self.age = self._calculate_age(self.birthdate)
        self.civilState = 1  # 婚姻状态 1:未婚, 2:已婚
        self.cat_gender_id = 2  # 性别 1:女性, 2:男性
        self.direction = "GUANGDONG GUANGZHOU BAIYUN"
        self.emergencyPerson = EmergencyPerson("YINAN", "LI", "185 1958 2008", "+86 185 1958 2008")