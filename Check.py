import sys
import time
import json
from datetime import datetime
import redis
import json
import argparse
from utils.Utils import Utils
from entities.Person import Person
from client.MexicoClient import MexicoClient


import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
print("install ChromeDriverManager")
ChromeDriverManager().install()
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


class Check:
    def __init__(self, office_id: int, sleep_time=10, reset_num=9, register_signal_type="hotmail"):
        self.office_id = office_id  # GUANGZHOU:246, BEIJING: 59, AUSTRIA:223, CANBERRA:74, RIO DE JANEIRO: 144
        self.sleep_time = sleep_time
        self.reset_num = reset_num
        self.register_signal_type = register_signal_type
        self.person = Person(office_id)
        print("check_citas_homepage..")
        self.check_citas_homepage()

    def check_citas_homepage(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--password-store=basic")  # 禁用密钥环
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--start-maximized")
        driver = uc.Chrome(options=chrome_options, verify=False)

        while True:
            try:
                driver.get("https://citas.sre.gob.mx/")
                driver.maximize_window()
                login_link = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Oficinas Consulares')]"))
                )
                login_link.click()
                break
            except Exception as e:
                pass
                print("Sign in按钮未能获取")
                time.sleep(3)
        print("check citas homepage success!")
        driver.quit()

    def check_visas_and_save_data(self):
        registered_account_list = "0_check_registered_account"
        register_request_signal = "0_check"
        if self.register_signal_type == "gmail":
            register_request_signal += "_gmail_register_signal"
        else:
            register_request_signal += "_hotmail_register_signal"
        used_account = "1_used_account"

        # Connect to Redis
        redis_conn = redis.Redis(host='47.254.14.124', port=6379, db=0, password='2023@mexico')
        redis_conn.select(0)
        while True:
            print("Reading account.", datetime.now())
            # read a raw account from redis
            registered_account = ""
            while not registered_account:
                registered_account = redis_conn.lpop(registered_account_list)
                if not registered_account:
                    print(f"can not find registered_account account [{registered_account_list}]")
                    time.sleep(3)
            print("find account:", registered_account)
            redis_conn.rpush(register_request_signal, "1")

            account_info = json.loads(registered_account)
            email = account_info["email"]
            email_pwd = account_info.get("email_pwd", "")
            password = account_info["password"]

            client = MexicoClient(email, password, self.person)
            while True:
                error_code1 = client.login_with_recaptcha_with_error_code()
                if error_code1 in [101, 102, 104, 105, 200]:
                    break
                time.sleep(3)
            if error_code1 in [101, 102, 104, 105]:
                print("account error, choose new account!")
                time.sleep(3)
                continue

            verify_response = client.verify_user()
            if verify_response.get("success", True) is False:
                print(f"verifyResponse: {verify_response}")
                time.sleep(5)
                continue

            check_count = 0
            max_check_count = 45
            while True:
                redis_conn.ping()
                check_count += 1

                if check_count >= max_check_count:
                    print("arrive max check count, change account!")
                    break

                if check_count % self.reset_num == 0:
                    while True:
                        error_code2 = client.login_with_recaptcha_with_error_code()
                        if error_code2 in [101, 102, 104, 105, 200]:
                            break
                        time.sleep(3)
                    if error_code2 in [101, 102, 104, 105]:
                        break

                    verify_response = client.verify_user()
                    if verify_response.get("success", True) is False:
                        print(f"verifyResponse: {verify_response}")
                        break

                print("time:"+str(datetime.now()), "check_count: " + str(check_count))
                check_code = client.check_visas_with_auth_by_error_code(self.office_id)
                print(f"checkCode: {check_code}")

                if check_code == -1:
                    check_count -= 1
                    time.sleep(1)
                    continue
                elif check_code == -2:
                    print("skip this account! sleep 10 seconds!")
                    time.sleep(10)
                    break
                elif check_code == -3:
                    print("don't sleep,next try!")
                elif check_code == 0:
                    if (check_count + 1) % self.reset_num != 0:
                        time.sleep(self.sleep_time)
                elif check_code == 1:
                    print("Found visas[sin][con]!!")
                    print("check save_data1!!")
                    error_code = client.save_data1()
                    if error_code == 1:
                        print("find save_data_right!")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_sin_real", "find save_data")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_con_real", "find save_data")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_sin", "find save_data")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_con", "find save_data")
                elif check_code == 2:
                    print("Found visas[sin]!!")
                    print("check save_data1!!")
                    error_code = client.save_data1()
                    if error_code == 1:
                        print("find save_data_right!")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_sin_real", "find save_data")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_sin", "find save_data")
                elif check_code == 3:
                    print("Found visas[con]!!")
                    print("check save_data1!!")
                    error_code = client.save_data1()
                    if error_code == 1:
                        print("find save_data_right!")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_con_real", "find save_data")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_con", "find save_data")

            print("hereererererererere")
            redis_conn.rpush(used_account, registered_account)

    def check_visas_by_date(self):
        registered_account_list = "0_check_registered_account"
        register_request_signal = "0_check"
        if self.register_signal_type == "gmail":
            register_request_signal += "_gmail_register_signal"
        else:
            register_request_signal += "_hotmail_register_signal"
        used_account = "1_used_account"

        # Connect to Redis
        redis_conn = redis.Redis(host='47.254.14.124', port=6379, db=0, password='2023@mexico')
        redis_conn.select(0)
        while True:
            print("Reading account.", datetime.now())
            # read a raw account from redis
            registered_account = ""
            while not registered_account:
                registered_account = redis_conn.lpop(registered_account_list)
                if not registered_account:
                    print(f"can not find registered_account account [{registered_account_list}]")
                    time.sleep(3)
            print("find account:", registered_account)
            redis_conn.rpush(register_request_signal, "1")

            account_info = json.loads(registered_account)
            email = account_info["email"]
            email_pwd = account_info.get("email_pwd", "")
            password = account_info["password"]

            # 能够获取trakingId的office
            # GUANGZHOU:246, BEIJING: 59, AUSTRIA:223, CANBERRA:74, RIO DE JANEIRO: 144, SHANGHAI: 164,
            person = Person(144)
            client = MexicoClient(email, password, person)
            while True:
                error_code1 = client.login_with_recaptcha_with_error_code()
                if error_code1 in [101, 102, 104, 105, 200]:
                    break
                time.sleep(3)
            if error_code1 in [101, 102, 104, 105]:
                print("account error, choose new account!")
                time.sleep(1)
                continue

            verify_response = client.verify_user()
            if verify_response.get("success", True) is False:
                print(f"verifyResponse: {verify_response}")
                continue
            # 获取trakingId
            client.save_data1()
            check_count = 0
            max_check_count = 45
            while True:
                redis_conn.ping()
                check_count += 1

                if check_count >= max_check_count:
                    print("arrive max check count, change account!")
                    break

                if check_count % self.reset_num == 0:
                    while True:
                        error_code2 = client.login_with_recaptcha_with_error_code()
                        if error_code2 in [101, 102, 104, 105, 200]:
                            break
                        time.sleep(3)
                    if error_code2 in [101, 102, 104, 105]:
                        break

                    verify_response = client.verify_user()
                    if verify_response.get("success", True) is False:
                        print(f"verifyResponse: {verify_response}")
                        break
                    # 获取trakingId
                    client.save_data1()

                print("time:" + str(datetime.now()), "check_count: " + str(check_count))
                check_code = client.check_visas_with_auth_by_error_code(self.office_id)
                print(f"checkCode: {check_code}")

                if check_code == -1:
                    check_count -= 1
                    time.sleep(1)
                    continue
                elif check_code == -2:
                    print("skip this account! sleep 10 seconds!")
                    time.sleep(10)
                    break
                elif check_code == -3:
                    print("don't sleep,next try!")
                elif check_code == 0:
                    if (check_count + 1) % self.reset_num != 0:
                        time.sleep(self.sleep_time)
                elif check_code == 1:
                    print("Found visas[sin][con]!!")
                    real_found = False
                    if len(client.get_office_event_with_office_id_and_formalitites_type(self.office_id, "con")) > 0:
                        real_found = True
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_con_real", "find save_data")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_con", "find save_data")
                        print(f"墨西哥【{self.person.dst_office.var_cad_oficina}】" + "[con]放号了！")
                    if len(client.get_office_event_with_office_id_and_formalitites_type(self.office_id, "sin")) > 0:
                        real_found = True
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_sin_real", "find save_data")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_sin", "find save_data")
                        print(f"墨西哥【{self.person.dst_office.var_cad_oficina}】" + "[sin]放号了！")
                    if real_found:
                        time.sleep(10)
                elif check_code == 2:
                    print("Found visas[sin]!!")
                    real_found = False
                    if len(client.get_office_event_with_office_id_and_formalitites_type(self.office_id, "sin")) > 0:
                        real_found = True
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_sin_real", "find save_data")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_sin", "find save_data")
                        print(f"墨西哥【{self.person.dst_office.var_cad_oficina}】" + "[sin]放号了！")
                    if real_found:
                        time.sleep(10)
                elif check_code == 3:
                    print("Found visas[con]!!")
                    real_found = False
                    if len(client.get_office_event_with_office_id_and_formalitites_type(self.office_id, "con")) > 0:
                        real_found = True
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_con_real", "find save_data")
                        redis_conn.rpush(f"{self.person.dst_office.var_cad_oficina}_check_visas_con", "find save_data")
                        print(f"墨西哥【{self.person.dst_office.var_cad_oficina}】" + "[con]放号了！")
                    if real_found:
                        time.sleep(10)
            print("hereererererererere")
            redis_conn.rpush(used_account, registered_account)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="input params")

    # check_office_id, sleep_time = 10, reset_num = 9, register_signal_type = "hotmail"
    # GUANGZHOU:246, BEIJING: 59, AUSTRIA:223, CANBERRA:74, RIO DE JANEIRO: 144, SHANGHAI: 164,
    parser.add_argument('office_id', type=int, help='运行模式')
    parser.add_argument('--sleep_time', type=int, default=10, help='sleep_time')
    parser.add_argument('--reset_num', type=int, default=9, help='reset_num')
    parser.add_argument('--mail_type', default='hotmail', choices=['hotmail', 'gmail'], help='register_signal_type')
    args = parser.parse_args()
    check = Check(args.office_id, args.sleep_time, args.reset_num, args.mail_type)
    check.check_visas_and_save_data()
    # check.check_visas_by_date()
