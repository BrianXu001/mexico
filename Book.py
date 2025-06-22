import json
import random
import socket
import time
from datetime import datetime, time as dt_time
import redis
import argparse
import pytz

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

beijing_tz = pytz.timezone('Asia/Shanghai')


class Book:
    def __init__(self):

        print("check_citas_homepage")
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

    def book_normal(self, specify_time, buffer_time):
        task_type = "book_normal"
        spl = specify_time.split(":")
        target_hour = int(spl[0])
        target_minute = int(spl[1])
        target_second = int(spl[2])

        extra_time = random.randint(0, buffer_time)
        print(extra_time)
        total_second = target_minute * 60 + target_second + extra_time
        target_minute = (total_second % 3600 // 60)
        target_second = (total_second % 3600 % 60)
        print("target_hour:", target_hour)
        print("target_minute:", target_minute)
        print("target_second:", target_second)
        now = datetime.now(beijing_tz)
        target_time = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)
        print("target_time:", target_time)

        registered_account_list = "0_check_registered_account"

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')} start task: {task_type}")
        ip_address = ""
        try:
            ip_address = socket.gethostbyname(socket.gethostname()) + "\n"
            print("ip_address:", ip_address)
        except socket.gaierror as e:
            print("Get ip address failed!")
            print(e)
        # Connect to Redis
        redis_client = redis.Redis(host='47.254.14.124', port=6379, db=0, password='2023@mexico')
        redis_client.select(0)
        # Read user info
        record = ""
        while not record:
            print("read client info..")
            record = redis_client.lpop("mexico_tasks")
            if not record:
                time.sleep(3)
        person_info = json.loads(record)
        person = Person(person_info)
        print(f"personInfo: {person_info}")
        while True:
            print(f"Get account..{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}")
            # read a raw account from redis
            registered_account = ""
            while not registered_account:
                registered_account = redis_client.lpop(registered_account_list)
                if not registered_account:
                    print(f"can not find registered_account account [{registered_account_list}]")
                    time.sleep(3)
            account_info = json.loads(registered_account)
            email = account_info["email"]
            email_pwd = account_info["email_pwd"]
            password = account_info["password"]

            client = MexicoClient(email, password, person)  # Assuming MexicoClient class is defined
            while True:
                error_code1 = client.login_with_recaptcha_with_error_code()
                if error_code1 in [101, 102, 104, 105, 200]:
                    break
                time.sleep(3)
            if error_code1 in [101, 102, 104, 105]:
                print("account error, choose new account")
                time.sleep(3)
                continue
            verify_response = client.verify_user()
            if "success" in verify_response and not verify_response["success"]:
                print(f"verifyResponse: {verify_response}")
                time.sleep(5)
                continue

            redis_client.lpush(
                client.CUSTOM_TASK_STATUS_LIST,
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}{task_type} {email} login success at {ip_address}"
            )

            count_check = 0
            begin_time = time.time()
            check_account = 0
            while True:
                count_check += 1
                # if (time.time() - start_time) > 59 * 60:  # 59 minutes
                #     print("This account is running 59 minutes, choose new account!(avoid being blocked)")
                #     break
                # Check visas
                if (time.time() - begin_time) > (check_account + 1) * (10 * 60):
                    check_code = client.check_visas_with_auth_by_error_code(client.person.dst_office.cat_office_id)
                    check_account += 1
                    if check_code == -2:
                        print("The account is blocked, need change!")
                        break
                # login again
                if (time.time() - begin_time) > 50 * 60:  # 30 minutes
                    while True:
                        error_code2 = client.login_with_recaptcha_with_error_code()
                        if error_code2 in [101, 102, 104, 105, 200]:
                            break
                        time.sleep(3)
                    if error_code2 in [101, 102, 104, 105]:
                        print("account error, choose new account")
                        break
                    verify_response = client.verify_user()
                    if "success" in verify_response and not verify_response["success"]:
                        print(f"verifyResponse: {verify_response}")
                        time.sleep(3)
                        break
                    begin_time = time.time()
                # check redis
                if redis_client.llen(f"{client.CHECK_LIST}_real") > 0:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')} find check visas!")
                elif datetime.now(beijing_tz) > target_time:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')} agreed time!")
                else:
                    print(f"当前时间 {datetime.now()} {count_check}")
                    time.sleep(3)
                    continue
                # start book
                client.do_book()
                break

            break




    def book_directly_appointment(self, specify_time, buffer_time):
        task_type = "book_normal"
        spl = specify_time.split(":")
        target_hour = int(spl[0])
        target_minute = int(spl[1])
        target_second = int(spl[2])

        extra_time = random.randint(0, buffer_time)
        print(extra_time)
        total_second = target_minute * 60 + target_second + extra_time
        target_minute = (total_second % 3600 // 60)
        target_second = (total_second % 3600 % 60)
        print("target_hour:", target_hour)
        print("target_minute:", target_minute)
        print("target_second:", target_second)
        now = datetime.now(beijing_tz)
        target_time = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)
        print("target_time:", target_time)

        registered_account_list = "0_check_registered_account"

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')} start task: {task_type}")
        ip_address = ""
        try:
            ip_address = socket.gethostbyname(socket.gethostname()) + "\n"
            print("ip_address:", ip_address)
        except socket.gaierror as e:
            print("Get ip address failed!")
            print(e)
        # Connect to Redis
        redis_client = redis.Redis(host='47.254.14.124', port=6379, db=0, password='2023@mexico')
        redis_client.select(0)



        # Read user info
        record = ""
        while not record:
            print("read client info..")
            record = redis_client.lpop("mexico_tasks")
            if not record:
                time.sleep(3)
        person_info = json.loads(record)
        person = Person(person_info)
        print(f"personInfo: {person_info}")

        while True:
            print(f"Get account..{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}")
            # read a raw account from redis
            registered_account = ""
            while not registered_account:
                registered_account = redis_client.lpop(registered_account_list)
                if not registered_account:
                    print(f"can not find registered_account account [{registered_account_list}]")
                    time.sleep(3)
            account_info = json.loads(registered_account)
            email = account_info["email"]
            email_pwd = account_info["email_pwd"]
            password = account_info["password"]

            client = MexicoClient(email, password, person)  # Assuming MexicoClient class is defined

            appointment_date = client.construct_date(redis_client, person)
            print("set appointment_date:", appointment_date)

            while True:
                error_code1 = client.login_with_recaptcha_with_error_code()
                if error_code1 in [101, 102, 104, 105, 200]:
                    break
                time.sleep(3)
            if error_code1 in [101, 102, 104, 105]:
                print("account error, choose new account")
                time.sleep(3)
                continue
            verify_response = client.verify_user()
            if "success" in verify_response and not verify_response["success"]:
                print(f"verifyResponse: {verify_response}")
                time.sleep(5)
                continue

            redis_client.lpush(
                client.CUSTOM_TASK_STATUS_LIST,
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}{task_type} {email} login success at {ip_address}"
            )

            count_check = 0
            begin_time = time.time()
            check_account = 0
            while True:
                count_check += 1
                # if (time.time() - start_time) > 59 * 60:  # 59 minutes
                #     print("This account is running 59 minutes, choose new account!(avoid being blocked)")
                #     break
                # Check visas
                if (time.time() - begin_time) > (check_account + 1) * (10 * 60):
                    check_code = client.check_visas_with_auth_by_error_code(client.person.dst_office.cat_office_id)
                    check_account += 1
                    if check_code == -2:
                        print("The account is blocked, need change!")
                        break
                # login again
                if (time.time() - begin_time) > 50 * 60:  # 30 minutes
                    while True:
                        error_code2 = client.login_with_recaptcha_with_error_code()
                        if error_code2 in [101, 102, 104, 105, 200]:
                            break
                        time.sleep(3)
                    if error_code2 in [101, 102, 104, 105]:
                        print("account error, choose new account")
                        break
                    verify_response = client.verify_user()
                    if "success" in verify_response and not verify_response["success"]:
                        print(f"verifyResponse: {verify_response}")
                        time.sleep(3)
                        break
                    begin_time = time.time()
                # check redis
                if redis_client.llen(f"{client.CHECK_LIST}_real") > 0:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')} find check visas!")
                elif datetime.now(beijing_tz) > target_time:
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')} agreed time!")
                else:
                    print(f"当前时间 {datetime.now()} {count_check}")
                    time.sleep(3)
                    continue
                # start book
                client.do_book_directly_appointment(appointment_date)
                break

            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="输入gmail账号、密码")
    parser.add_argument("arg1", help="specify_time")
    parser.add_argument("arg2", type=int, default=0, help="buffer_time/second")
    args = parser.parse_args()
    specify_time = args.arg1
    buffer_time = args.arg2
    book = Book()
    book.book_normal(specify_time, buffer_time)
