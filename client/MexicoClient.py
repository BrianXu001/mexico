import base64
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib

from urllib.parse import quote
import socket

from entities.Country import Country
from entities.State import State

from utils.Utils import Utils
from utils.Recaptcha import Recaptcha

import redis


class MexicoClient:
    def __init__(self, user_id: str = "", password: str = "", person=None):
        self.user_id = user_id
        self.password = password
        self.person = person
        self.register_user_info = {}
        self.citas_token = ""
        self.hash_id = ""
        self.hash_id_office_preference = ""
        self.traking_id = ""
        self.folio_procedure_initial = ""
        self.check_office_id = -1
        self.got_ticket = False
        self.send_email_count = 0
        self.key = "ca0d02b0df9839e77ae6ad1c1b48654c"

        if person and person.dst_office:
            self.AVAILABLE_CON_DAY_LIST = f"{person.dst_office.var_cad_oficina}_con_availableDay"
            self.AVAILABLE_SIN_DAY_LIST = f"{person.dst_office.var_cad_oficina}_sin_availableDay"
            self.POSSIBLE_TIME_SIN_LIST = f"{person.dst_office.var_cad_oficina}_possible_sin_times"
            self.POSSIBLE_TIME_CON_LIST = f"{person.dst_office.var_cad_oficina}_possible_con_times"
            self.CUSTOM_TASK_STATUS_LIST = f"{person.dst_office.var_cad_oficina}_custom_{person.full_name}"
            self.CUSTOM_TASK_FINISHED_LIST = f"{person.dst_office.var_cad_oficina}_custom_{person.full_name}finished"

            if person.formalities and person.formalities.formalitites_type_id == "10":
                self.CHECK_LIST = f"{person.dst_office.var_cad_oficina}_check_visas_sin"
            elif person.formalities and person.formalities.formalitites_type_id == "11":
                self.CHECK_LIST = f"{person.dst_office.var_cad_oficina}_check_visas_con"

            self.CHECK_VISAS_LIST = f"{person.dst_office.var_cad_oficina}_check_visas"

        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.rnd = random.Random()
        self.available_days = []
        self.events = []
        self.available_time = {}
        self.event_response = ""
        self.close_appointment_flag = False
        self.update_d5 = False
        self.d4 = {}

        # URLs
        self.login_url = "https://citasapi.sre.gob.mx/api/appointment/auth/login"
        self.general_url = "https://citasapi.sre.gob.mx/api/console/get-general"
        self.catalog_url = "https://citasapi.sre.gob.mx/api/catalog/v1/get-catalog"
        self.save_data_url = "https://citasapi.sre.gob.mx/api/appointment/v1/save-data"
        self.office_event_prefix_url = "https://citasapi.sre.gob.mx/api/console/office-events?"
        self.office_day_event_prefix_url = "https://citasapi.sre.gob.mx/api/console/office-day-events?"
        self.save_appointment_url = "https://citasapi.sre.gob.mx/api/appointment/v1/save-appointment"
        self.document_url = "https://citasapi.sre.gob.mx/api/appointment/v1/generate-documents"

    def get_headers(self) -> Dict[str, str]:
        return {
            "accept": "application/json",
            "accept-c": "true",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://citas.sre.gob.mx",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://citas.sre.gob.mx/",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-csrf-token": "",
            "x-requested-with": "XMLHttpRequest",
            "x-sre-api-key": "i3sid7ZQVsp0BPPC8yrdWqby5XZiRcu9"
        }

    def get_headers_with_auth(self) -> Dict[str, str]:
        headers = self.get_headers()
        if not self.citas_token:
            print("Do not have authorization. Please login first!")
        headers["authorization"] = f"Bearer {self.citas_token}"
        return headers

    def get_headers_get(self) -> Dict[str, str]:
        return {
            "accept": "application/json",
            "accept-c": "true",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "origin": "https://citas.sre.gob.mx",
            "pragma": "no-cache",
            "referer": "https://citas.sre.gob.mx/",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        }

    def get_headers_get_with_auth(self) -> Dict[str, str]:
        headers = self.get_headers_get()
        if not self.citas_token:
            print("Do not have authorization. Please login first!")
        headers["authorization"] = f"Bearer {self.citas_token}"
        return headers

    def generate_recaptcha_url(self, user_name: str) -> str:
        try:
            text_bytes = user_name.encode('utf-8')
            base64_encoded = base64.b64encode(text_bytes).decode('utf-8')
            return f"https://citasapi.sre.gob.mx/api/appointment/lang/get-captcha/{base64_encoded}"
        except Exception as e:
            print(f"Error generating recaptcha URL: {e}")
            return ""

    def get_recaptcha_code(self, user_name: str) -> str:
        get_captcha_url = self.generate_recaptcha_url(user_name)
        print("get_captcha_url:", get_captcha_url)
        headers = {
            "accept": "application/json",
            "accept-c": "true",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://citas.sre.gob.mx",
            "priority": "u=1, i",
            "referer": "https://citas.sre.gob.mx/",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-csrf-token": "",
            "x-requested-with": "XMLHttpRequest",
            "x-sre-api-key": "i3sid7ZQVsp0BPPC8yrdWqby5XZiRcu9"
        }

        response = requests.get(get_captcha_url, headers=headers)
        if response.status_code == 200:
            try:
                content = response.text
                decrypted_content = Utils.crypto_js_decrypt(content, self.key)
                data = json.loads(decrypted_content)
                img_data = data.get("img", "")[22:]  # Remove the data:image/png;base64, prefix
                return Recaptcha.recognize(img_data)

            except Exception as e:
                print(f"Error generating recaptcha pic: {e}")
                return ""
        else:
            print(f"Failed to get recaptcha image: {response.status_code}")
            return ""

    def login_with_recaptcha_with_error_code(self) -> int:
        print("======login======")
        try:
            print(f"username: {self.user_id} password: {self.password}")
            recaptcha_code = self.get_recaptcha_code(self.user_id)
            print("recaptcha_code:", recaptcha_code)
            user_info = {
                "email": self.user_id,
                "password": self.password,
                "location": "ext",
                "broser": "5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                "platform": "Linux x86_64",
                "lang": "zh",
                "atuh_login": True,
                "captcha": recaptcha_code
            }
            user_info_enc = Utils.crypto_js_encrypt(json.dumps(user_info), self.key)
            params = {"encrypt": user_info_enc}

            response = requests.post(
                self.login_url,
                headers=self.get_headers(),
                json=params
            )

            response_content = response.text
            if not response_content:
                print("empty response!")
                return 100

            decrypted_content = Utils.crypto_js_decrypt(response_content, self.key)
            if not decrypted_content:
                print("empty response!")
                return 100

            response_json = json.loads(decrypted_content)

            if "屏蔽" in decrypted_content:
                print(f"responseJson: {response_json}")
                return 101
            elif "Este usuário está bloqueado" in decrypted_content:
                print(f"responseJson: {response_json}")
                return 102
            elif "El Captcha no es correcto" in decrypted_content:
                print(f"responseJson: {response_json}")
                return 103
            elif "Se identifico un comportamiento" in decrypted_content:
                print(f"responseJson: {response_json}")
                return 104
            elif "Este usuario ha sido BLOQUEADO" in decrypted_content:
                print(f"responseJson: {response_json}")
                return 105
            else:
                print(f"responseJson: {response_json}")

            self.citas_token = response_json.get("citas_token", "")
            self.register_user_info = response_json.get("user", {})
            self.hash_id = self.register_user_info.get("hash", "")

            print(f"getStatusCode: {response.status_code}")
            print(f"citas_token: {self.citas_token}")
            print(f"registerUserInfo: {self.register_user_info}")
            print(f"hash_id: {self.hash_id}")
            print(f"login success {datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}")

            return 200
        except Exception as e:
            print("==login error1==>")
            print(e)
            return 300

    def get_save_data_request1(self) -> Dict:

        save_data = {
            "id": None,
            "origin": 1,
            "people_total": 0,
            "hash_appointment_family_id": None,
            "relationship_id": None,
            "typeAppointment": 1,
            "awaitStep": True,
            "folioProcedureInitial": None,
            "selectedForm": False,
            "country_id": self.person.dst_country.country_id,
            "country_data": self.get_country_data(),
            "state_id": self.person.dst_state.state_id,
            "state_data": self.get_state_data(),
            "cat_office_id": self.person.dst_office.cat_office_id,
            "cat_office_data": self.get_office_data_new(),
            "folioAppointment": None,
            "dateAppointment": None,
            "hourStarAppointment": None,
            "hourEndAppointment": None,
            "created_by_id": None,
            "cat_apmt_type_appointment_id": None,
            "office_selected": True,
            "people": self.get_people_data1_new(),
            "officeConfigData": self.get_office_config_data1(self.person.dst_office.cat_office_id),
            "setTempFormalitiesConsole": self.get_set_temp_formalities_console(),
            "step": 1
        }
        return save_data

    def get_country_data(self) -> Dict:
        return {
            "idalpha3": self.person.dst_country.idalpha3,
            "idalpha2": self.person.dst_country.idalpha2,
            "tiene_edos": self.person.dst_country.tiene_edos,
            "id_pais": self.person.dst_country.id_pais,
            "cad_nombre_es": self.person.dst_country.cad_nombre_es
        }

    def get_state_data(self) -> Dict:
        return {
            "var_cad_tipo_entidad": self.person.dst_state.var_cad_tipo_entidad,
            "var_id_tipo_entidad": self.person.dst_state.var_id_tipo_entidad,
            "var_cad_entidad": self.person.dst_state.var_cad_entidad,
            "var_oficina": self.person.dst_state.var_oficina,
            "var_id_pais": self.person.dst_state.var_id_pais,
            "var_id_entidad": self.person.dst_state.var_id_entidad
        }

    def get_office_data_new(self) -> Dict:
        return {
            "var_cad_num_interior": "Floor 17",
            "var_cad_localidad": None,
            "id_continente": 3,
            "id_oficina_padre": None,
            "var_num_longitud": self.person.dst_office.var_num_longitud,
            "var_cad_municipio_alcaldia": None,
            "var_cad_entidad_federativa": self.person.dst_office.var_cad_entidad_federativa,
            "cad_tipo_oficina": "Sección Consular",
            "var_id_codigo_postal": None,
            "is_ome": False,
            "var_cad_num_telefono": self.person.dst_office.var_cad_num_telefono,
            "nombre_corto": "Embamex China",
            "var_id_entidad_federativa": self.person.dst_office.var_id_entidad_federativa,
            "continente": "Asia",
            "var_id_oficina": self.person.dst_office.var_id_oficina,
            "var_cad_codigo_postal": "00000",
            "var_cad_oficina": self.person.dst_office.var_cad_oficina,
            "var_cad_correo_electronico": "embamexcor@gmail.com",
            "id_tipo_oficina": 12,
            "id_region": 4,
            "var_id_municipio_alcaldia": None,
            "cad_nombre_oficial": "Embajada de México en China",
            "var_cad_calle": "Tianhe Road, Teem Tower Unit 01",
            "var_id_localidad": None,
            "var_cad_num_exterior": "6",
            "var_cad_colonia": " Jongno-gu",
            "region": "Asia-Pacífico",
            "var_num_latitud": self.person.dst_office.var_num_latitud,
            "id_pais": self.person.dst_country.country_id,
            "id_unidad_administrativa": 2,
            "unidad_administrativa": "Subsecretaría de Relaciones Exteriores",
            "observations": [""]
        }

    def get_people_data1_new(self) -> List[Dict]:
        return [{
            "id": None,
            "people_total": 0,
            "hash_appointment_family_id": None,
            "relationship_id": None,
            "curp": "",
            "fullName": self.person.full_name,
            "name": self.person.name,
            "firstName": self.person.first_name,
            "lastName": "",
            "birthdate": self.person.birthdate,
            "age": self.person.age,
            "statusCurp": None,
            "docProbatorio": None,
            "isValidateCurp": None,
            "additional_person": False,
            "naturalized": None,
            "disability": None,
            "civilState": self.person.civil_state,
            "firstNameMarried": "",
            "adoption": None,
            "cat_gender_id": self.person.cat_gender_id,
            "cat_nationality_id": Country.country_to_id.get(self.person.nationality),
            "created_by_id": None,
            "cat_apmt_type_person_id": None,
            "apmt_persons_suet_formalities_status": False,
            "showForm": True,
            "apmt_persons_tmp_renapo_search_curp": False,
            "country_id": Country.country_to_id.get(self.person.country_of_birth),
            "state_id": State.state_to_id.get(self.person.state_of_birth),
            "municipality_id": State.state_to_id.get(
                self.person.municipality_of_birth) if self.person.municipality_of_birth else None,
            "locality_id": None,
            "colony_id": None,
            "location": None,
            "postalCode": None,
            "street": None,
            "outdoorNumber": None,
            "interiorNumber": None,
            "passportNummber": None,
            "email": self.user_id,
            "phone": self.register_user_info.get("person", {}).get("primary_phone", {}).get("phone", ""),
            "cell_phone": None,
            "annotations": None,
            "step": None,
            "aceptNotificacionPhone": False,
            "persons_formalities": [],
            "apmt_persons_suet_tmp_formalities": self.get_apmt_persons_suet_tmp_formalities(),
            "apmt_persons_data_address_home": self.get_apmt_persons_data_address_home1(),
            "apmt_persons_data_address_emergency": self.get_apmt_persons_data_address_emergency1(),
            "apmt_persons_additional": self.get_apmt_persons_additional(),
            "apmt_persons_second_additional": self.get_apmt_persons_second_additional1(),
            "apmt_persons_documents": self.get_apmt_persons_documents()
        }]

    def get_apmt_persons_suet_tmp_formalities(self) -> List[Dict]:
        return [
            self.gen_tramite_data("31", "Visas", "11", "Con permiso del INM (Validación vía servicio web con el INM)",
                                  "", "", "2"),
            self.gen_tramite_data("39", "Pasaporte y/o credencial para votar", "", "", "", "", ""),
            self.gen_tramite_data("31", "Visas", "10", "Sin permiso del INM", "20", "Residente temporal", "2"),
            self.gen_tramite_data("31", "Visas", "10", "Sin permiso del INM", "17",
                                  "Visitante sin permiso para realizar actividades remuneradas", "2")
        ]

    def gen_tramite_data(self, t_id_tramite: str, t_cad_tramite: str, t_id_tipo_tramite: str,
                         t_cad_tipo_tramite: str, t_id_subtipo_tramite: str,
                         t_cad_subtipo_tramite: str, t_id_tipo_nacionalidad: str) -> Dict:
        return {
            "t_id_tramite": int(t_id_tramite) if t_id_tramite else None,
            "t_cad_tramite": t_cad_tramite if t_cad_tramite else None,
            "t_id_tipo_tramite": int(t_id_tipo_tramite) if t_id_tipo_tramite else None,
            "t_cad_tipo_tramite": t_cad_tipo_tramite if t_cad_tipo_tramite else None,
            "t_id_subtipo_tramite": int(t_id_subtipo_tramite) if t_id_subtipo_tramite else None,
            "t_cad_subtipo_tramite": t_cad_subtipo_tramite if t_cad_subtipo_tramite else None,
            "t_id_tipo_nacionalidad": int(t_id_tipo_nacionalidad) if t_id_tipo_nacionalidad else None,
            "t_num_edad_inicial": 0,
            "t_num_edad_final": 150,
            "t_vigencias": None,
            "t_descuentos": None
        }

    def get_apmt_persons_data_address_home1(self) -> Dict:
        return {
            "country_id": None,
            "postal_code": None,
            "state_id": None,
            "municipality_id": None,
            "colony_id": None,
            "direction": None,
            "street": None,
            "outdoor_number": None,
            "interior_number": None
        }

    def get_apmt_persons_data_address_emergency1(self) -> Dict:
        return {
            "name": "",
            "firstName": "",
            "lastName": "",
            "email": None,
            "phone": None,
            "cell_phone": None,
            "sameDirection": None,
            "country_id": None,
            "postal_code": None,
            "state_id": None,
            "municipality_id": None,
            "colony_id": None,
            "direction": None,
            "street": None,
            "outdoor_number": None,
            "interior_number": None
        }

    def get_apmt_persons_additional(self) -> Dict:
        return {
            "id": None,
            "curp": None,
            "name": "",
            "firstName": "",
            "lastName": "",
            "birthdate": None,
            "cat_apmt_gender_id": None,
            "country_id": None,
            "cat_nationality_id": None,
            "parentesco_id": None,
            "parentesco_name": None,
            "doc_complementario_id": None,
            "doc_complementario_name": None,
            "doc_probatorio_id": None,
            "doc_probatorio_name": None,
            "doc_nacionalidad_id": None,
            "doc_nacionalidad_name": None,
            "modelo_rubros_dinamico_doc_complementario": {},
            "modelo_rubros_dinamico_doc_probatorio": {},
            "modelo_rubros_dinamico_doc_nacionalidad": {},
            "modelo_rubros_dinamico_doc_acta_extemporanea": {}
        }

    def get_apmt_persons_second_additional1(self) -> Dict:
        return {
            "id": None,
            "curp": None,
            "name": "",
            "firstName": "",
            "lastName": "",
            "birthdate": None,
            "cat_apmt_gender_id": None,
            "country_id": None,
            "cat_nationality_id": None,
            "parentesco_id": None,
            "parentesco_name": None,
            "doc_complementario_id": None,
            "doc_complementario_name": None,
            "doc_probatorio_id": None,
            "doc_probatorio_name": None,
            "doc_nacionalidad_id": None,
            "doc_nacionalidad_name": None,
            "modelo_rubros_dinamico_doc_complementario": {},
            "modelo_rubros_dinamico_doc_probatorio": {},
            "modelo_rubros_dinamico_doc_nacionalidad": {},
            "modelo_rubros_dinamico_doc_acta_extemporanea": {}
        }

    def get_apmt_persons_documents(self) -> Dict:
        return {
            "doc_complementario_id": None,
            "doc_complementario_name": None,
            "doc_probatorio_id": None,
            "doc_probatorio_name": None,
            "doc_nacionalidad_id": None,
            "doc_nacionalidad_name": None,
            "modelo_rubros_dinamico_doc_complementario": {},
            "modelo_rubros_dinamico_doc_probatorio": {},
            "modelo_rubros_dinamico_doc_nacionalidad": {},
            "modelo_rubros_dinamico_doc_acta_extemporanea": {}
        }

    def get_office_config_data1(self, office_id: int) -> Dict:
        while True:
            try:
                url = "https://citasapi.sre.gob.mx/api/console/office-preferences"
                request_info = Utils.crypto_js_encrypt(json.dumps(self.gen_office_info(office_id)), self.key)
                params = {"encrypt": request_info}

                response = requests.post(
                    url,
                    headers=self.get_headers_with_auth(),
                    json=params
                )

                response_content = response.text
                decrypted_content = Utils.crypto_js_decrypt(response_content, self.key)
                response_json = json.loads(decrypted_content)
                print(f"getOfficePreference: {response_json}")
                if "success" in response_json and response_json.get("success"):
                    if "office_preferences" in response_json:
                        return response_json.get("office_preferences")
                if "Unauthenticated" in  decrypted_content:
                    return {}
                print("try [get_office_config_data1] again")
                time.sleep(3)
            except Exception as e:
                print(e)
                print("try [get_office_config_data1] again")
                time.sleep(3)

    def gen_office_info(self, office_id: int) -> Dict:
        return {
            "officeId": office_id,
            "api_key": "M5hxYq16KRyKfGHSlKzf4d7I92SUwBA02s6fxZg4YGkgsT4sEm2kME5L1alrpB8LuVxjawsGvojISFpRzZGjcDA8ELk9a1xTJKUk"
        }

    def get_set_temp_formalities_console(self) -> Dict:
        while True:
            try:
                request_info = Utils.crypto_js_encrypt(self.gen_general_info(self.person.dst_office.cat_office_id), self.key)
                params = {"encrypt": request_info}

                response = requests.post(
                    self.general_url,
                    headers=self.get_headers_with_auth(),
                    json=params
                )

                response_content = response.text
                decrypted_content = Utils.crypto_js_decrypt(response_content, self.key)
                response_json = json.loads(decrypted_content)
                print(f"get_general_response:{response_json}")
                return response_json
            except Exception as e:
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}getGeneralResponse error==> {e}")
                print("try [get_general_response] again")
                time.sleep(3)

    # def get_general_response(self, office_id: int, thread_info: str) -> Dict:
    #     while True:
    #         try:
    #             request_info = Utils.crypto_js_encrypt(self.gen_general_info(office_id), self.key)
    #             params = {"encrypt": request_info}
    #
    #             response = requests.post(
    #                 self.general_url,
    #                 headers=self.get_headers_with_auth(),
    #                 json=params
    #             )
    #
    #             response_content = response.text
    #             decrypted_content = Utils.crypto_js_decrypt(response_content, self.key)
    #             response_json = json.loads(decrypted_content)
    #             print(f"get_general_response:{response_json}")
    #             return response_json
    #         except Exception as e:
    #             print(f"{thread_info}{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}getGeneralResponse error==> {e}")
    #             print("try [get_general_response] again")

    def send_email(self, subject: str, text: str) -> None:
        if self.send_email_count <= 1:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}Sending Email...")

            from_address = "519335189@qq.com"
            username = "519335189@qq.com"
            password = "svcjgppiolmfcahc"
            to_address2 = "519335189@qq.com"

            msg = MIMEMultipart()
            msg['From'] = from_address
            msg['To'] = to_address2
            msg['Subject'] = subject

            msg.attach(MIMEText(text, 'plain'))

            try:
                with smtplib.SMTP_SSL('smtp.qq.com', 465) as server:
                    server.login(username, password)
                    server.send_message(msg)
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}Send Email Success!")
                self.send_email_count += 1
            except Exception as e:
                print(f"Error sending email: {e}")

    def send_email_with_attachment(self, subject: str, text: str, attachment_bytes: bytes,
                                   attachment_name: str) -> None:
        if self.send_email_count == 0:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}Sending Email...")

            from_address = "519335189@qq.com"
            username = "519335189@qq.com"
            password = "svcjgppiolmfcahc"
            to_address2 = "519335189@qq.com"

            msg = MIMEMultipart()
            msg['From'] = from_address
            msg['To'] = to_address2
            msg['Subject'] = subject

            msg.attach(MIMEText(text, 'plain'))

            part = MIMEApplication(attachment_bytes, Name=attachment_name)
            part['Content-Disposition'] = f'attachment; filename="{attachment_name}"'
            msg.attach(part)

            try:
                with smtplib.SMTP_SSL('smtp.qq.com', 465) as server:
                    server.login(username, password)
                    server.send_message(msg)
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}Send Email Success!")
                self.send_email_count += 1
            except Exception as e:
                print(f"Error sending email with attachment: {e}")

    def verify_user(self):
        url = "https://citasapi.sre.gob.mx/api/appointment/v1/verify-user-data"
        headers = {
            "accept": "application/json",
            "accept-c": "true",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "authorization": f"Bearer {self.citas_token}",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://citas.sre.gob.mx",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://citas.sre.gob.mx/",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-csrf-token": "",
            "x-requested-with": "XMLHttpRequest",
            "x-sre-api-key": "i3sid7ZQVsp0BPPC8yrdWqby5XZiRcu9"
        }

        try:
            response = requests.post(url, headers=headers)
            response_content = response.text
            decrypted_content = Utils.crypto_js_decrypt(response_content, self.key)

            if not decrypted_content:
                print("verify_user empty response!")
                return {}
            else:
                print(f"verify response: {decrypted_content}")
            response_json = json.loads(decrypted_content)
            return response_json
        except Exception as e:
            print("==verify_user error==>", str(e))
            return {}

    def gen_general_info(self, office_id):
        general_info = {
            "officeId": office_id,  # 246:GuangZhou
            "pcm_event_id": None,
            "cat_system_id": 1,
            "api_key": "M5hxYq16KRyKfGHSlKzf4d7I92SUwBA02s6fxZg4YGkgsT4sEm2kME5L1alrpB8LuVxjawsGvojISFpRzZGjcDA8ELk9a1xTJKUk"
        }
        return json.dumps(general_info)

    def get_general_response_with_auth_by_error_code(self, office_id):
        try:
            request_info = Utils.crypto_js_encrypt(self.gen_general_info(office_id), self.key)
            params = {
                "encrypt": request_info
            }

            response = requests.post(
                self.general_url,
                headers=self.get_headers_with_auth(),
                json=params
            )
            response_content = response.content
            decrypted_content = Utils.crypto_js_decrypt(response_content, self.key)
            response_json = json.loads(decrypted_content)
            response_json["errorCode"] = "0"
        except Exception as e:
            print(f"getGeneralResponse error==> {e}")
            response_json = {"errorCode": "1"}
            return response_json

        return response_json

    def check_visas_with_auth_by_error_code(self, office_id):
        try:
            general_response = self.get_general_response_with_auth_by_error_code(office_id)
            print(general_response)

            error_code = ""
            if "errorCode" in general_response:
                error_code = general_response["errorCode"]

            if error_code == "1":
                return -1
            if "error" in general_response and general_response["error"] == "Unauthenticated":
                return -2
            if ("success" in general_response and not general_response["success"] and general_response["message"] == "No se pudo mostrar información"):
                return -3

            available_procedures = general_response["availableProcedures"]

            find_sin = False
            find_con = False
            for procedure_group in available_procedures:
                for procedure in procedure_group:
                    cat_procedure_name = procedure["cat_procedure_name"].strip().lower()
                    cat_procedure_type_name = "None" if procedure["cat_procedure_type_name"] is None else procedure["cat_procedure_type_name"].strip().lower()

                    if "visas" in cat_procedure_name:
                        print(f"cat_procedure_type_name: {cat_procedure_type_name}")
                        if "sin" in cat_procedure_type_name:
                            find_sin = True
                        if "con" in cat_procedure_type_name:
                            find_con = True
                        if cat_procedure_type_name is None or cat_procedure_type_name == "None":
                            find_sin = True
                            find_con = True

            if find_sin and find_con:
                return 1
            elif find_sin:
                return 2
            elif find_con:
                return 3
            else:
                return 0
        except Exception as e:
            print("check_visas_with_auth_by_error_code error!!!")
            return 0

    def save_data1(self):
        while True:
            try:
                request_info = Utils.crypto_js_encrypt(json.dumps(self.get_save_data_request1()), self.key)
                params = {
                    "encrypt": request_info
                }
                response = requests.post(
                    self.save_data_url,
                    headers=self.get_headers_with_auth(),
                    json=params
                )
                response_content = response.content
                decrypted_content = Utils.crypto_js_decrypt(response_content, self.key)
                print(f"{str(datetime.now())} save1_response: {decrypted_content}")
                if not decrypted_content:
                    print("save_data1 empty response!")
                    time.sleep(5)
                    continue

                response_json = json.loads(decrypted_content)
                if "error" in response_json and response_json["error"] == "Unauthenticated":
                    print("账号异常")
                    return 2
                if "success" in response_json and response_json["success"]:
                    print("got save_data_right!!!")
                    self.traking_id = response_json["id"]
                    print(f"trakingId1: {self.traking_id}")
                    return 1
                print("try save_data1 again")
                time.sleep(5)

            except Exception as e:
                print("==save_data1 error==>")
                print(e)
                print("try [save_data1] again")
                time.sleep(5)

    def get_date_data_with_office_id_and_formalitites_type(self, office_id: int, formalitites_type):
        # formalitites_type: sin, con
        date_data = {
            "cat_office_id": office_id,
            "pcm_event_id": None,  # Equivalent to JSONNull.getInstance()
        }
        if formalitites_type == "sin":
            procedure = {
                "cat_procedure_id": 31,
                "cat_procedure_type_id": 10,
                "cat_procedure_subtype_id": 17,
                "cat_procedure_name": "Visas",
                "cat_procedure_type_name": "Sin permiso del INM",
                "cat_procedure_subtype_name": "Visitante sin permiso para realizar actividades remuneradas"
            }
        else:
            procedure = {
                "cat_procedure_id": 31,
                "cat_procedure_type_id": 11,
                "cat_procedure_subtype_id": None,
                "cat_procedure_name": "Visas",
                "cat_procedure_type_name": "Con permiso del INM (Validación vía servicio web con el INM)",
                "cat_procedure_subtype_name": None
            }

        date_data["procedures"] = [procedure]  # Equivalent to JSONArray with one element
        date_data["amountFormaliti"] = 1

        return date_data

    def get_date_data(self):
        date_data = {
            "cat_office_id": self.person.dst_office.cat_office_id,
            "pcm_event_id": None,  # Equivalent to JSONNull.getInstance()
        }

        procedure = {
            "cat_procedure_id": self.person.formalities.formalitites_id,
            "cat_procedure_type_id": self.person.formalities.formalitites_type_id,
            "cat_procedure_subtype_id": None if not self.person.formalities.formalitites_subtype_id else self.person.formalities.formalitites_subtype_id,
            "cat_procedure_name": self.person.formalities.formalitites_name,
            "cat_procedure_type_name": self.person.formalities.formalitites_type_name,
            "cat_procedure_subtype_name": None if not self.person.formalities.formalitites_subtype_name else self.person.formalities.formalitites_subtype_name
        }

        date_data["procedures"] = [procedure]  # Equivalent to JSONArray with one element
        date_data["amountFormaliti"] = 1

        return date_data

    def gen_office_event_request_info_with_recaptcha_code(self, recaptcha_code: str, office_id: int, formalitites_type) -> str:
        # Create date objects
        now = datetime.now()
        date_90_days_later = now + timedelta(days=90)

        # Format dates as 'YYYY-MM-DD'
        start_date = now.strftime("%Y-%m-%d")
        end_date = date_90_days_later.strftime("%Y-%m-%d")

        api_key = "M5hxYq16KRyKfGHSlKzf4d7I92SUwBA02s6fxZg4YGkgsT4sEm2kME5L1alrpB8LuVxjawsGvojISFpRzZGjcDA8ELk9a1xTJKUk"

        # Create the JSON data structure
        json_data = {
            "currentView": "dayGridMonth",
            "interval": {"startDate": start_date,"endDate": end_date},
            "dateData": self.get_date_data_with_office_id_and_formalitites_type(office_id, formalitites_type),
            "cat_system_id": "1",
            "procces_id": self.traking_id,
            "captcha_value": recaptcha_code,
            "usr": self.hash_id,
            "people_total": None,  # Equivalent to JSONNull.getInstance()
            "api_key": api_key
        }

        return json.dumps(json_data)

    def valid_recaptcha(self, recaptcha_code):
        url = "https://citasapi.sre.gob.mx/api/appointment/v1/validate-captcha"
        # Create the payload
        user_info = {"captcha": recaptcha_code}
        user_info_enc = Utils.crypto_js_encrypt(json.dumps(user_info), self.key)  # You'll need to implement the encrypt function
        # Prepare request parameters
        params = {"encrypt": user_info_enc}
        try:
            # Make the POST request with headers (you'll need to implement get_headers_with_auth)
            response = requests.post(url, headers=self.get_headers_with_auth(), json=params)
            decrypted_content = Utils.crypto_js_decrypt(response.text, self.key)
            response_json = json.loads(decrypted_content)

            print(f"valid_recaptcha response: {response_json}")
            return response_json

        except Exception as e:
            print("valid recaptcha error!")
            print(e)
            return {}

    def get_office_event_with_office_id_and_formalitites_type(self, office_id: int, formalitites_type):
        # print(f"{thread_info}{formatter.format(datetime.now())}_getOfficeEventResponse")
        # date_list = []
        while True:
            try:
                recaptcha_code = self.get_recaptcha_code(self.user_id)
                print(datetime.now(), f"recaptcha_code:{recaptcha_code}")
                if not recaptcha_code:
                    time.sleep(5)
                    continue
                valid_response = self.valid_recaptcha(recaptcha_code)
                if "error" not in valid_response or str(valid_response["error"]).lower() != "ok":
                    continue

                request_info = self.gen_office_event_request_info_with_recaptcha_code(recaptcha_code, office_id, formalitites_type)
                request_info = Utils.crypto_js_encrypt(request_info, self.key)
                encrypted_params = quote(request_info, encoding="utf-8")
                url = f"{self.office_event_prefix_url}encryptParams={encrypted_params}"
                response = requests.get(url, headers=self.get_headers_with_auth())
                response_content = response.content
                print(f"responseContent:{response_content}")

                if not response_content:
                    print("empty response")
                    return []

                decrypted_content = Utils.crypto_js_decrypt(response_content, self.key)
                print(f"check response:{decrypted_content}")
                response_json = json.loads(decrypted_content)
                office_events = response_json.get("events", [])
                events = json.loads(json.dumps(office_events))  # Convert to ensure it's a list
                print("events:", events)
                if events and events[0] != "null":
                    try:
                        # Convert to list of dicts for sorting
                        json_list = [event for event in events if isinstance(event, dict)]
                        # Sort by availables_by_day in descending order
                        json_list.sort(key=lambda x: x.get("availables_by_day", 0), reverse=True)
                        return json_list
                    except Exception as e:
                        print(f"{datetime.now()}==getDateError1==>")
                        return []

            except Exception as e:
                print(e)
                return []

        return []

    def get_date_data(self):
        date_data = {
            "cat_office_id": self.person.dst_office.cat_office_id,
            "pcm_event_id": None,  # Equivalent to JSONNull.getInstance()

            "procedures": [
                {
                    "cat_procedure_id": self.person.formalities.formalitites_id,
                    "cat_procedure_type_id": self.person.formalities.formalitites_type_id,
                    "cat_procedure_subtype_id": self.person.formalities.formalitites_subtype_id if self.person.formalities.formalitites_subtype_id else None,
                    "cat_procedure_name": self.person.formalities.formalitites_name,
                    "cat_procedure_type_name": self.person.formalities.formalitites_type_name,
                    "cat_procedure_subtype_name": self.person.formalities.formalitites_subtype_name if self.person.formalities.formalitites_subtype_name else None
                }
            ],
            "amountFormaliti": 1
        }
        return date_data

    def gen_office_day_event_request_info_with_recaptcha_code(self, selected_date, recaptcha_code):
        api_key = "M5hxYq16KRyKfGHSlKzf4d7I92SUwBA02s6fxZg4YGkgsT4sEm2kME5L1alrpB8LuVxjawsGvojISFpRzZGjcDA8ELk9a1xTJKUk"
        request_info = {
            "selectedDate": selected_date,
            "dateData": self.get_date_data(),  # Assuming you have this function defined elsewhere
            "cat_system_id": 1,
            "captcha_value": recaptcha_code,
            "usr": self.hash_id,  # Assuming this is part of a class
            "procces_id": self.traking_id,  # Assuming this is part of a class
            "api_key": api_key
        }
        return json.dumps(request_info)

    def get_office_days(self,selected_date, recaptcha_code ):
        request_info = self.gen_office_day_event_request_info_with_recaptcha_code(selected_date, recaptcha_code)
        request_info = Utils.crypto_js_encrypt(request_info, self.key)
        encrypted_params = quote(request_info, encoding="utf-8")
        url = f"{self.office_event_prefix_url}encryptParams={encrypted_params}"
        response = requests.get(url, headers=self.get_headers_with_auth())
        response_content = response.content
        print(f"responseContent:{response_content}")

        if not response_content:
            print("empty response")
            return []

        decrypted_content = Utils.crypto_js_decrypt(response_content, self.key)
        print(f"check response:{decrypted_content}")
        response_json = json.loads(decrypted_content)
        return response_json

    def get_days_with_selected_date(self, selected_date):
        while True:
            try:
                recaptcha_code = self.get_recaptcha_code(self.user_id)
                print(datetime.now(), f"recaptcha_code:{recaptcha_code}")
                if not recaptcha_code:
                    time.sleep(5)
                    continue
                valid_response = self.valid_recaptcha(recaptcha_code)
                if "error" not in valid_response or str(valid_response["error"]).lower() != "ok":
                    continue

                dates = []
                times = self.get_office_days(selected_date, recaptcha_code).get("events")


                times_array = json.loads(times) if isinstance(times, str) else times
                if isinstance(times_array, list) and times_array:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} getOfficeDayEventResponse==>{json.dumps(times_array)}")
                    for item in times_array:
                        if "0" in item:
                            for key, value in item.items():
                                dates.append(json.loads(value) if isinstance(value, str) else value)
                        else:
                            dates.append(item)
                else:
                    times_object = json.loads(times) if isinstance(times, str) else times
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} getOfficeDayEventResponse==>{json.dumps(times_object)}")
                    for key, value in times_object.items():
                        dates.append(json.loads(value) if isinstance(value, str) else value)
                return dates
            except Exception as e:
                print(e)
                return []

    def gen_date_object(self, date: dict) -> dict:
        date_data = {}
        try:
            if date:  # Check if dictionary is not empty
                # Copy all key-value pairs from input date
                date_data.update(date)

                # Add start and end times
                date_data["start"] = f"{date['date']}T{date['initialTime']}"
                date_data["end"] = f"{date['date']}T{date['endTime']}"

        except Exception as e:
            date_data = {}
            # Assuming the first value in the dictionary contains the needed data
            for entry_value in date.values():
                if isinstance(entry_value, dict):
                    temp_data = entry_value
                else:
                    try:
                        temp_data = json.loads(entry_value)
                    except:
                        continue

                # Copy all key-value pairs from temp_data
                date_data.update(temp_data)

                # Add start and end times
                date_data["start"] = f"{temp_data['date']}T{temp_data['initialTime']}"
                date_data["end"] = f"{temp_data['date']}T{temp_data['endTime']}"
                break  # Only process first entry as per original Java code

        return date_data

    def get_date(self):
        formalitites_type_name_simple = "sin" if "sin" in self.person.formalities.formalitites_type_name.lower() else "con"
        events = self.get_office_event_with_office_id_and_formalitites_type(self.person.dst_office.cat_office_id, formalitites_type_name_simple)

        if len(events) > 0:
            days = self.get_days_with_selected_date(events[0])
            if len(days) > 0:
                date_wrap = self.gen_date_object(days[0])
                return date_wrap
        return {}

    def get_process(self):
        url = "https://citasapi.sre.gob.mx/api/appointment/v1/get-process"
        data = {
            "id": self.traking_id
        }

        while True:
            try:
                request_info = Utils.crypto_js_encrypt(json.dumps(data), self.key)
                # Prepare request parameters
                params = {
                    "encrypt": request_info
                }
                response = requests.post(url, headers=self.get_headers_with_auth(), json=params)

                response_content = response.text
                decrypted_content = Utils.crypto_js_decrypt(response_content, self.key)
                response_json = json.loads(decrypted_content)
                if response_json.get("success", False):
                    return response_json
                else:
                    print("get_process failed, sleep 3 seconds!")
                    time.sleep(3)

            except Exception as e:
                print("==get_process error==>")
                print(str(e))  # Print the actual error for debugging
                print("get_process failed, sleep 3 seconds!")
                time.sleep(3)

    def gen_sub_data(self, t_id_tramite: str, t_cad_tramite: str,
                     t_id_tipo_tramite: str, t_cad_tipo_tramite: str,
                     t_id_subtipo_tramite: str, t_cad_subtipo_tramite: str,
                     t_id_tipo_nacionalidad: str) -> dict:
        data1 = {
            "t_id_subtipo_tramite": None if not t_id_subtipo_tramite else t_id_subtipo_tramite,
            "t_cad_subtipo_tramite": None if not t_cad_subtipo_tramite else t_cad_subtipo_tramite
        }

        tmp_array = [
            self.gen_tramite_data(t_id_tramite, t_cad_tramite,
                                  t_id_tipo_tramite, t_cad_tipo_tramite,
                                  t_id_subtipo_tramite, t_cad_subtipo_tramite,
                                  t_id_tipo_nacionalidad)
        ]

        data1["data"] = tmp_array
        return data1

    def gen_data_sin(self, t_id_tramite: str, t_cad_tramite: str,
                     t_id_tipo_tramite: str, t_cad_tipo_tramite: str,
                     t_id_tipo_nacionalidad: str) -> dict:
        t_id_subtipo_tramite1 = "17"
        t_cad_subtipo_tramite1 = "Visitante sin permiso para realizar actividades remuneradas"
        t_id_subtipo_tramite2 = "20"
        t_cad_subtipo_tramite2 = "Residente temporal"

        data2 = {
            "t_id_tipo_tramite": t_id_tipo_tramite,
            "t_cad_tipo_tramite": t_cad_tipo_tramite
        }

        data = [
            self.gen_sub_data(t_id_tramite, t_cad_tramite, t_id_tipo_tramite,
                              t_cad_tipo_tramite, t_id_subtipo_tramite1,
                              t_cad_subtipo_tramite1, t_id_tipo_nacionalidad),
            self.gen_sub_data(t_id_tramite, t_cad_tramite, t_id_tipo_tramite,
                              t_cad_tipo_tramite, t_id_subtipo_tramite2,
                              t_cad_subtipo_tramite2, t_id_tipo_nacionalidad)
        ]

        data2["data"] = data

        return data2

    def gen_data_con(self, t_id_tramite: str, t_cad_tramite: str,
                     t_id_tipo_tramite: str, t_cad_tipo_tramite: str,
                     t_id_tipo_nacionalidad: str) -> dict:
        t_id_subtipo_tramite1 = ""
        t_cad_subtipo_tramite1 = ""

        data2 = {
            "t_id_tipo_tramite": t_id_tipo_tramite,
            "t_cad_tipo_tramite": t_cad_tipo_tramite
        }

        data = [
            self.gen_sub_data(t_id_tramite, t_cad_tramite,
                              t_id_tipo_tramite, t_cad_tipo_tramite,
                              t_id_subtipo_tramite1, t_cad_subtipo_tramite1,
                              t_id_tipo_nacionalidad)
        ]

        data2["data"] = data

        return data2

    def get_visas_data(self, t_id_tramite: str, t_cad_tramite: str, t_id_tipo_nacionalidad: str) -> list:
        data = []

        t_id_tipo_tramite1 = "10"
        t_cad_tipo_tramite1 = "Sin permiso del INM"
        t_id_tipo_tramite2 = "11"
        t_cad_tipo_tramite2 = "Con permiso del INM (Validación vía servicio web con el INM)"

        tmp_data = self.gen_data_sin(t_id_tramite, t_cad_tramite,
                                     t_id_tipo_tramite1, t_cad_tipo_tramite1,
                                     t_id_tipo_nacionalidad)

        tmp_data2 = self.gen_data_con(t_id_tramite, t_cad_tramite,
                                      t_id_tipo_tramite2, t_cad_tipo_tramite2,
                                      t_id_tipo_nacionalidad)

        data.append(tmp_data)
        data.append(tmp_data2)

        return data

    def get_persons_formalities_temp_data(self):
        t_id_tramite = "31"
        t_cad_tramite = "Visas"
        t_id_tipo_nacionalidad = "2"

        temp_data = {
            "t_id_tramite": t_id_tramite,
            "t_cad_tramite": t_cad_tramite,
            "data": self.get_visas_data(t_id_tramite, t_cad_tramite, t_id_tipo_nacionalidad)
        }

        return temp_data

    def get_persons_formalities_by_step2(self):
        person_data = []
        data = {
            "id": None,
            "formalitites_id": self.person.formalities.formalitites_id,
            "formalitites_name": self.person.formalities.formalitites_name,
            "formalitites_type_id": self.person.formalities.formalitites_type_id,
            "formalitites_type_name": self.person.formalities.formalitites_type_name,
            "formalitites_subtype_id": None if not self.person.formalities.formalitites_subtype_id else self.person.formalities.formalitites_subtype_id,
            "formalitites_subtype_name": None if not self.person.formalities.formalitites_subtype_name else self.person.formalities.formalitites_subtype_name,
            "passportNumber": None if not self.person.formalities.passportNumber else self.person.formalities.passportNumber,
            "nud": None if not self.person.formalities.nud else self.person.formalities.nud,
            "validity_id": None,
            "validity_name": None,
            "discount_id": None,
            "discount_name": None,
            "discount_formalitites_id": None,
            "discount_formalitites_name": None,
            "amount": None,
            "coin_name": None,
            "coin_id": None,
            "document_formalitites_id": None,
            "document_formalitites_name": None,
            "temp_data": self.get_persons_formalities_temp_data()
        }

        person_data.append(data)
        return person_data

    def get_apmt_persons_select_tmp_formalities(self):
        person_data = []
        temp_data = self.get_persons_formalities_temp_data()
        person_data.append(temp_data)
        return person_data

    def get_save_data_request2(self, d1):
        # Assuming d1 is a dictionary parsed from JSON
        data = d1["data"]
        json_data = data["json"]

        # Modify the json data
        json_data["folioProcedureInitial"] = data["folioProcedureInitial"]
        json_data["selectedForm"] = True
        json_data["people"][0]["persons_formalities"] = self.get_persons_formalities_by_step2()
        json_data["people"][0]["apmt_persons_select_tmp_formalities"] = self.get_apmt_persons_select_tmp_formalities()
        json_data["step"] = 2
        json_data["step_token"] = json_data["step_token"]
        json_data["trakingId"] = self.traking_id
        json_data["diffMin"] = d1["segundos"]

        return json_data

    def save_data2(self, d1: dict):
        while True:
            try:
                # Prepare request data
                request_data = self.get_save_data_request2(d1)
                request_info = Utils.crypto_js_encrypt(json.dumps(request_data), self.key)
                params = {"encrypt": request_info}
                headers = self.get_headers_with_auth()

                response = requests.post(
                    self.save_data_url,
                    headers=headers,
                    json=params,
                    timeout=10  # Added timeout for safety
                )
                decrypted_content = Utils.crypto_js_decrypt(response.text, self.key)
                print(f"{str(datetime.now())} save2_response: {decrypted_content}")
                if not decrypted_content:
                    print("save_data2 empty response!")
                    time.sleep(5)
                    continue

                response_json = json.loads(decrypted_content)
                if "error" in response_json and response_json["error"] == "Unauthenticated":
                    print("账号异常")
                    return 2
                if "success" in response_json and response_json["success"]:
                    return 1
                print("try save_data2 again")
                time.sleep(5)

            except Exception as e:
                print("==save_data_2 error==>")
                print(str(e))
                time.sleep(5)

    def get_apmt_persons_second_additional_3(self) -> dict:
        person_data = {
            "doc_complementario_id": None,
            "doc_complementario_name": None,
            "doc_probatorio_id": None,
            "doc_probatorio_name": None,
            "doc_nacionalidad_id": None,
            "doc_nacionalidad_name": None,
            "modelo_rubros_dinamico_doc_complementario": [],
            "modelo_rubros_dinamico_doc_probatorio": [],
            "modelo_rubros_dinamico_doc_nacionalidad": [],
            "modelo_rubros_dinamico_doc_acta_extemporanea": [],
            "name": None,
            "firstName": None,
            "lastName": None,
            "birthdate": None,
            "cat_apmt_gender_id": None,
            "country_id": None,
            "cat_nationality_id": None
        }
        return person_data

    def get_value1_data(self) -> dict:
        value_1_data = {
            "id_doc_probatorio": 142,
            "id_rubro": 36,
            "cad_rubro": "Número",
            "id_tipo_objeto": 9,
            "cad_tipo": "number",
            "num_longitud": 20,
            "id_tipo_dato": 3,
            "cad_tipo_dato": "integer",
            "id_tipo_validacion": None,
            "cad_tipo_validacion": None,
            "b64_rubro": None
        }
        return value_1_data

    def get_value2_data(self) -> dict:
        value_2_data = {
            "id_doc_probatorio": 142,
            "id_rubro": 41,
            "cad_rubro": "Fecha de expedición",
            "id_tipo_objeto": 4,
            "cad_tipo": "datetime-local",
            "num_longitud": 10,
            "id_tipo_dato": 2,
            "cad_tipo_dato": "varchar",
            "id_tipo_validacion": None,
            "cad_tipo_validacion": None,
            "b64_rubro": None
        }
        return value_2_data

    def get_value3_data(self) -> dict:
        value_3_data = {
            "id_doc_probatorio": 142,
            "id_rubro": 42,
            "cad_rubro": "Fecha de vencimiento",
            "id_tipo_objeto": 4,
            "cad_tipo": "datetime-local",
            "num_longitud": 10,
            "id_tipo_dato": 2,
            "cad_tipo_dato": "varchar",
            "id_tipo_validacion": None,
            "cad_tipo_validacion": None,
            "b64_rubro": None
        }
        return value_3_data

    def get_value4_data(self) -> dict:
        value_4_data = {
            "id_doc_probatorio": 142,
            "id_rubro": 96,
            "cad_rubro": "País de expedición",
            "id_tipo_objeto": 10,
            "cad_tipo": "",
            "num_longitud": 0,
            "id_tipo_dato": 3,
            "cad_tipo_dato": "integer",
            "id_tipo_validacion": None,  # Note: Fixed typo from original (validacion -> validacion)
            "cad_tipo_validacion": None,
            "b64_rubro": None
        }
        return value_4_data

    def get_doc_proof(self) -> dict:
        doc_proof = {
            "value_1": self.person.identification,
            "value_1_data": self.get_value1_data(),
            "value_2": self.person.id_begin_date,
            "value_2_data": self.get_value2_data(),
            "value_3": self.person.id_end_date,
            "value_3_data": self.get_value3_data(),
            "value_4": "China",
            "value_4_data": self.get_value4_data()
        }
        return doc_proof
    def get_apmt_persons_documents_real(self) -> dict:
        person_data = {
            "doc_complementario_id": None,
            "doc_complementario_name": None,
            "doc_probatorio_id": 142,
            "doc_probatorio_name": "Documento de identidad nacional (DNI)",
            "doc_nacionalidad_id": None,
            "doc_nacionalidad_name": None,
            "modelo_rubros_dinamico_doc_complementario": {},
            "modelo_rubros_dinamico_doc_probatorio": self.get_doc_proof(),
            "modelo_rubros_dinamico_doc_nacionalidad": {},
            "modelo_rubros_dinamico_doc_acta_extemporanea": {}
        }
        return person_data

    def get_save_data_request3(self, d2: dict) -> dict:
        json_data = d2["data"]["json"]

        # Access and modify nested data
        people_array = json_data["people"]
        first_person = people_array[0]

        first_person.update({
            "naturalized": False,
            "disability": False
        })

        # Modify formalities data
        if first_person.get("persons_formalities"):
            first_person["persons_formalities"][0]["id_tramite"] = self.person.formalities.formalitites_type_id

        # Add additional data
        first_person.update({
            "apmt_persons_second_additional": self.get_apmt_persons_second_additional_3(),
            "apmt_persons_documents": self.get_apmt_persons_documents_real()
        })

        # Update top-level fields
        json_data.update({
            "step": 3,
            "step_token": json_data["step_token"],
            "trakingId": self.traking_id,
            "diffMin": d2["segundos"]
        })

        return json_data

    def save_data3(self, d2: dict):
        while True:
            try:
                # Prepare request data
                request_data = self.get_save_data_request3(d2)
                request_info = Utils.crypto_js_encrypt(json.dumps(request_data), self.key)
                # Prepare params and headers
                params = {"encrypt": request_info}
                headers = self.get_headers_with_auth()
                # Make POST request
                response = requests.post(
                    self.save_data_url,
                    headers=headers,
                    json=params,
                    timeout=10  # Added timeout for safety
                )

                decrypted_content = Utils.crypto_js_decrypt(response.text, self.key)
                print(f"{str(datetime.now())} save3_response: {decrypted_content}")
                if not decrypted_content:
                    print("save_data3 empty response!")
                    time.sleep(5)
                    continue

                response_json = json.loads(decrypted_content)
                if "error" in response_json and response_json["error"] == "Unauthenticated":
                    print("账号异常")
                    return 2
                if "success" in response_json and response_json["success"]:
                    return 1
                print("try save_data3 again")
                time.sleep(5)

            except Exception as e:
                print("==save_data_3 error==>")
                print(str(e))
                time.sleep(5)

    def get_apmt_persons_data_address_home(self) -> dict:
        person_data = {
            "country_id": self.person.from_country.country_id,  # Current country
            "postal_code": None,
            "state_id": self.person.from_state.state_id,  # Current state/province
            "municipality_id": None,
            "colony_id": None,
            "direction": self.person.direction,  # Address direction
            "street": None,
            "outdoor_number": None,
            "interior_number": None
        }
        return person_data

    def get_apmt_persons_data_address_emergency(self) -> dict:
        emergency_person = self.person.emergency_person

        person_data = {
            "name": emergency_person.name,
            "firstName": emergency_person.first_name,
            "lastName": "",  # Empty string as specified
            "email": None,
            "phone": emergency_person.phone,
            "cell_phone": None,
            "sameDirection": True,  # Boolean value
            "country_id": None,
            "postal_code": None,
            "state_id": None,
            "municipality_id": None,
            "colony_id": None,
            "direction": None,
            "street": None,
            "outdoor_number": None,
            "interior_number": None,
            "cellPhoneFormatInternational": emergency_person.cell_phone_format_international
        }
        return person_data

    def get_save_data_request4(self, d3: dict) -> dict:
        json_data = d3["data"]["json"]
        people_array = json_data["people"]
        first_person = people_array[0]

        # Update person data
        first_person.update({
            "apmt_persons_data_address_home": self.get_apmt_persons_data_address_home(),
            "apmt_persons_data_address_emergency": self.get_apmt_persons_data_address_emergency()
        })

        # Update top-level fields
        json_data.update({
            "step": 4,
            "step_token": json_data["step_token"],
            "trakingId": self.traking_id,
            "diffMin": d3["segundos"]
        })

        return json_data

    def save_data4(self, d3: dict):
        while True:
            try:
                # Prepare request data
                request_data = self.get_save_data_request4(d3)
                request_info = Utils.crypto_js_encrypt(json.dumps(request_data), self.key)

                # Prepare request components
                params = {"encrypt": request_info}
                headers = self.get_headers_with_auth()
                # Make POST request with timeout
                response = requests.post(
                    self.save_data_url,
                    headers=headers,
                    json=params,
                    timeout=10  # 10 second timeout
                )

                decrypted_content = Utils.crypto_js_decrypt(response.text, self.key)
                print(f"{str(datetime.now())} save4_response: {decrypted_content}")
                if not decrypted_content:
                    print("save_data4 empty response!")
                    time.sleep(5)
                    continue

                response_json = json.loads(decrypted_content)
                if "error" in response_json and response_json["error"] == "Unauthenticated":
                    print("账号异常")
                    return 2
                if "success" in response_json and response_json["success"]:
                    return 1
                print("try save_data4 again")
                time.sleep(5)

            except Exception as e:
                print("==save_data_4 error==>")
                print(str(e))
                time.sleep(5)

    def get_new_schedule(self, date):
        new_schedule = {}
        # new_schedule["id"] = int(date["hash_id"])  # commented out as in original
        new_schedule["newDateSelected"] = date["date"]
        new_schedule["newTimeSelected"] = date["initialTime"][:5]
        new_schedule["newEndTimeSelected"] = date["endTime"][:5]
        new_schedule["mainProcedureSelected"] = ""
        new_schedule["fullDate"] = f"{date['date']}T{date['initialTime']}"

        return new_schedule

    def get_save_data_request5(self, d4, date):
        data = d4["data"]
        json_data = data["json"]

        json_data["awaitStep"] = False
        json_data["step"] = 4
        json_data["step_token"] = json_data["step_token"]
        json_data["trakingId"] = self.traking_id
        json_data["diffMin"] = d4["segundos"]
        json_data["GrecaptchaResponse"] = None  # Using None instead of JSONNull
        json_data["newSchedule"] = self.get_new_schedule(date)
        json_data["program"] = True

        return json_data

    def save_data5(self, d4: dict, date: dict):
        while True:
            try:
                # Prepare request data
                request_data = self.get_save_data_request5(d4, date)
                request_info = Utils.crypto_js_encrypt(json.dumps(request_data), self.key)

                # Prepare request components
                params = {"encrypt": request_info}
                headers = self.get_headers_with_auth()
                # Make POST request with timeout
                response = requests.post(
                    self.save_data_url,
                    headers=headers,
                    json=params,
                    timeout=10  # 10 second timeout
                )

                decrypted_content = Utils.crypto_js_decrypt(response.text, self.key)
                print(f"{str(datetime.now())} save5_response: {decrypted_content}")
                if not decrypted_content:
                    print("save_data5 empty response!")
                    time.sleep(5)
                    continue

                response_json = json.loads(decrypted_content)
                if "error" in response_json and response_json["error"] == "Unauthenticated":
                    print("账号异常")
                    return {}
                if "success" in response_json and response_json["success"]:
                    return response_json
                print("try save_data5 again")
                time.sleep(5)

            except Exception as e:
                print("==save_data_5 error==>")
                print(str(e))
                time.sleep(5)

    def get_appointment_request(self, d5: dict, date: dict) -> dict:
        submit_info = {}
        date_new = {}

        # date_new["id"] = int(date["hash_id"])  # commented out as in original
        date_new["start"] = date["start"]
        date_new["end"] = date["end"]

        submit_info["date"] = date_new
        submit_info["form"] = d5["data"]
        submit_info["newSchedule"] = self.get_new_schedule(date)

        # Set null values for form fields
        form = submit_info["form"]
        null_fields = [
            "id",
            "folioAppointment",
            "dateAppointment",
            "hourStarAppointment",
            "hourEndAppointment",
            "created_by_id",
            "cat_apmt_type_appointment_id"
        ]

        for field in null_fields:
            form[field] = None  # Using None instead of JSONNull

        return submit_info

    def get_pdf_request(self, ticket_id: str, d5: dict) -> dict:
        pdf_request = {
            "folio": ticket_id,
            "form": d5["data"]
        }
        return pdf_request

    def get_ticket_pdf_bytes(self, ticket_id: str, d5: dict) -> bytes:
        while True:
            try:
                pdf_request = self.get_pdf_request(ticket_id, d5)
                request_info = Utils.crypto_js_encrypt(json.dumps(pdf_request), self.key)

                # Prepare request components
                params = {"encrypt": request_info}
                headers = self.get_headers_with_auth()
                # Make POST request with timeout
                response = requests.post(
                    self.document_url,
                    headers=headers,
                    json=params,
                    timeout=10  # 10 second timeout
                )
                decrypted_content = Utils.crypto_js_decrypt(response.text, self.key)
                # Parse response and extract PDF bytes
                response_json = json.loads(decrypted_content)
                file_str = response_json["file"]
                pdf_bytes = base64.b64decode(file_str)
                return pdf_bytes
            except Exception as e:
                print(e)
                time.sleep(5)

    def save_appointment_with_pdf(self, d5: dict, date: dict):
        while True:
            try:
                # Prepare request data
                request_data = self.get_appointment_request(d5, date)
                request_info = Utils.crypto_js_encrypt(json.dumps(request_data), self.key)

                # Prepare request components
                params = {"encrypt": request_info}
                headers = self.get_headers_with_auth()
                # Make POST request with timeout
                response = requests.post(
                    self.save_appointment_url,
                    headers=headers,
                    json=params,
                    timeout=10  # 10 second timeout
                )

                decrypted_content = Utils.crypto_js_decrypt(response.text, self.key)
                print(f"{str(datetime.now())} save_appointment: {decrypted_content}")
                if not decrypted_content:
                    print("save_appointment empty response!")
                    time.sleep(5)
                    continue

                response_json = json.loads(decrypted_content)
                if "error" in response_json and response_json["error"] == "Unauthenticated":
                    print("账号异常")
                    return 2
                if "success" in response_json and response_json["success"]:
                    if "ticket" in response_json and response_json["ticket"]:
                        # Write to Redis
                        redis_conn = redis.Redis(host='47.254.14.124', port=6379, db=0, password='2023@mexico')
                        redis_conn.select(0)
                        redis_conn.rpush(
                            self.CUSTOM_TASK_FINISHED_LIST,
                            f"{str(datetime.now())} {self.user_id} got ticket!"
                        )

                        # Save PDF
                        pdf_bytes = self.get_ticket_pdf_bytes(response_json["ticket"], d5)
                        file_path = (
                            f"./{self.person.first_name} {self.person.name}_"
                            f"{response_json['date']}.pdf"
                        )

                        try:
                            with open(file_path, "wb") as f:
                                f.write(pdf_bytes)
                            print("save pdf success!")
                        except IOError as e:
                            print(e)

                        # Send email
                        self.got_ticket = True
                        subject = f"{self.person.first_name} {self.person.name}-墨西哥预约抢票成功！"
                        text = (
                            f"{self.person.first_name} {self.person.name}\n"
                            f"{json.dumps(response_json, indent=2, ensure_ascii=False)}\n"
                        )

                        addr_text = "Got at ip address:"
                        try:
                            addr_text += f"{socket.gethostbyname(socket.gethostname())}\n"
                        except socket.error as e:
                            print(e)

                        text += (
                            f"{addr_text}\n"
                            f"userId: {self.user_id}    password:{self.password}\n"
                            f"手续类型：{self.person.formalities.formalitites_type_name}\n"
                        )

                        attachment_name = (
                            f"{self.person.first_name} {self.person.name}_"
                            f"{response_json['date']}.pdf"
                        )
                        self.send_email_with_attachment(
                            subject, text, pdf_bytes, attachment_name
                        )
                        return True

                    return False
                print("try save_appointment again")
                time.sleep(5)

            except Exception as e:
                print("==save_appointment error==>")
                print(str(e))
                time.sleep(5)
                print("终止")
                break

    def do_book(self):
        self.save_data1()
        start_time = time.time()
        time.sleep(5)
        d1 = self.get_process()
        time.sleep(5)

        self.save_data2(d1)
        time.sleep(5)
        d2 = self.get_process()
        time.sleep(5)

        self.save_data3(d2)
        time.sleep(5)
        d3 = self.get_process()
        time.sleep(5)

        elapsed_time = (time.time()) - start_time
        if elapsed_time < 60:
            sleep_time = 60 - elapsed_time
            print(f"sleep {sleep_time} seconds!")
            time.sleep(sleep_time)

        self.save_data4(d3)
        d4 = self.get_process()

        appointment_date = self.get_date()
        d5 = self.save_data5(d4, appointment_date)

        self.save_appointment_with_pdf(d5, appointment_date)


if __name__ == "__main__":
    # {"email":"ambfvcqhs8@hotmail.com","email_pwd":"mbc599534","password":"mbc5995341@Gmail"}
    # {"email":"aqnfe63@hotmail.com","email_pwd":"kyh478984","password":"kyh4789841@Gmail"}
    # {"email":"exwpchxjho4@hotmail.com","email_pwd":"gsy184641","password":"gsy1846411@Gmail"}
    client = MexicoClient(user_id="exwpchxjho4@hotmail.com", password="gsy1846411@Gmail")
    client.login_with_recaptcha_with_error_code()