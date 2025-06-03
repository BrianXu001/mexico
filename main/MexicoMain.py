import json
import time
import random
import requests
import redis
from datetime import datetime, time as datetime_time
from typing import List, Dict, Optional, Tuple
import base64
import os
import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import re

from client import MexicoClient


class MexicoMain:

    @staticmethod
    def book_with_registered_account(email_type: str, specify_time: str):
        task_type = "signal"
        print(f"specify_time: {specify_time}")

        target_hour, target_minute = 0, 0
        if ":" in specify_time:
            target_hour, target_minute = map(int, specify_time.split(":"))

        target_time = datetime_time(target_hour, target_minute)

        # Redis keys
        registered_account_list = "0_registered_account_list_book"
        register_request_signal = "0_register_request_signal_book_hotmail" if email_type == "hotmail" else "0_register_request_signal_book"
        used_account = "1_used_account"

        # Initialize
        formatter = "%Y-%m-%d %H:%M:%S:%f"
        print(f"{datetime.now().strftime(formatter)} start task: {task_type}")

        # Get IP address
        ip_address = "unknown"
        try:
            ip_address = requests.get('https://api.ipify.org').text
        except Exception as e:
            print(f"Get IP address failed: {e}")

        # Load properties
        properties = {
            "notice_redis_host": "47.254.14.124",
            "notice_redis_db": "0",
            "notice_redis_pwd": "2023@mexico",
            "user_info_redis_task_list": "user_info_task_list"
        }

        # Connect to Redis
        r = redis.Redis(
            host=properties["notice_redis_host"],
            port=6379,
            db=int(properties["notice_redis_db"]),
            password=properties["notice_redis_pwd"]
        )

        # Read person info
        record = None
        while not record:
            print("read client info..")
            record = r.lpop(properties["user_info_redis_task_list"])
            if not record:
                time.sleep(3)
                continue

        person_info = json.loads(record)
        person = person_info  # In Python we can use dict directly

        book_success = False
        max_account_num = 1
        try_count = 0

        while True:
            print(f"Get account.. {datetime.now().strftime(formatter)}")

            # Get registered account
            registered_account = None
            while not registered_account:
                registered_account = r.lpop(registered_account_list)
                if not registered_account:
                    print(f"can not find registered_account account [{registered_account_list}]")
                    time.sleep(3)
                    continue

            r.rpush(register_request_signal, "1")

            account_info = json.loads(registered_account)
            email = account_info["email"]
            email_pwd = account_info["email_pwd"]
            password = account_info["password"]

            # Store in Redis
            r.set(f"{email}_booking", registered_account)

            client = MexicoClient(email, password, person, properties)

            # Login with recaptcha
            error_code1 = -1
            while True:
                error_code1 = client.login_with_recaptcha_with_error_code()
                if error_code1 in [101, 102, 104, 105, 200]:
                    break
                time.sleep(1)

            if error_code1 in [101, 102, 104, 105]:
                r.delete(f"{email}_booking")
                time.sleep(1)
                continue

            verify_response = client.verify_user()
            if verify_response.get("success", False) is False:
                print(f"verifyResponse: {verify_response}")
                r.delete(f"{email}_booking")
                continue

            r.lpush(client.CUSTOM_TASK_STATUS_LIST,
                    f"{datetime.now().strftime(formatter)}{task_type} {email} login success at {ip_address}")

            count_check = 0
            begin_time = time.time()
            start_time = time.time()
            check_account = 0

            while True:
                count_check += 1

                if (time.time() - start_time) > 59 * 60:  # 59 minutes
                    print("This account is running 59 minutes, choose new account!")
                    break

                # Check visas periodically
                if (time.time() - begin_time) > (check_account + 1) * (5 * 60):
                    check_code = client.checkVisasWithAuthByErrorCode(
                        client.person["dstOffice"]["cat_office_id"],
                        "main",
                        count_check
                    )
                    check_account += 1
                    if check_code == -2:
                        print("The account is blocked, need change!")
                        break

                if (time.time() - begin_time) > 30 * 60:
                    error_code2 = -1
                    while True:
                        error_code2 = client.login_with_recaptcha_with_error_code()
                        if error_code2 in [101, 102, 104, 105, 200]:
                            break
                        time.sleep(1)

                    if error_code2 in [101, 102, 104, 105]:
                        break

                    verify_response = client.verify_user()
                    if verify_response.get("success", False) is False:
                        print(f"verifyResponse: {verify_response}")
                        break

                    begin_time = time.time()

                current_time = datetime.now().time()
                if (r.llen(f"{client.CHECK_LIST}_real") > 0 or
                        (":" in specify_time and (current_time >= target_time))):
                    print(f"{datetime.now().strftime(formatter)} find check visas!")
                else:
                    print(f"Current time {current_time} target time {target_time}")
                    if count_check % 1 == 0:
                        print(
                            f"{datetime.now().strftime(formatter)} check [{client.CHECK_LIST}_real] count: {count_check}")
                    time.sleep(3)
                    continue

                # Do pre-request
                while True:
                    d4 = client.doPreRequest("main_")
                    if d4:
                        client.d4 = d4
                        client.closeAppointmentFlag = False
                        client.updateD5 = True
                        print("doPreRequest success!")
                        break
                    else:
                        print("doPreRequest failed! sleep 5 seconds!")
                        time.sleep(5)

                # Get available dates
                if not client.getDateLocal_with_recaptcha("", r, client):
                    time.sleep(3)

                if "date" not in client.availableTime:
                    print("Can not find date!")
                    return

                day = client.availableTime["date"]
                if (day < client.person["start_time"] or
                        day > client.person["end_time"]):
                    print("The date is out of demand!")
                    return

                date_wrap = client.genDateObjcet(client.availableTime)
                d5 = client.save_data5(client.d4, date_wrap)
                req = client.getAppointmentRequest(d5, date_wrap)
                request_info = client.encrypt(json.dumps(req))

                book_done = client.save_appointment_with_pdf(request_info, "", r, d5)
                try_count += 1

                if book_done:
                    book_success = True
                    break

                if try_count >= max_account_num:
                    break

            r.rpush(used_account, registered_account)
            r.delete(f"{email}_booking")
            print(f"book tryCount: {try_count} bookSuccess: {book_success}")

            if book_success or try_count >= max_account_num:
                break

    @staticmethod
    def check_visas_and_save_data_with_account(args: List[str]):
        check_office_id = int(args[0])
        sleep_time = int(args[1])
        reset_num = int(args[2]) if len(args) >= 3 else 9
        mail_type = args[3] if len(args) >= 4 else "hotmail"

        registered_account_list = "0_registered_account_list_check"
        register_request_signal = "0_register_request_signal_check_hotmail" if mail_type == "hotmail" else "0_register_request_signal_check"
        used_account = "1_used_account"

        formatter = "%Y-%m-%d %H:%M:%S:%f"

        # Load properties and connect to Redis
        properties = {
            "notice_redis_host": "47.254.14.124",
            "notice_redis_db": "0",
            "notice_redis_pwd": "2023@mexico",
            "user_info_redis_task_list": "user_info_task_list"
        }

        r = redis.Redis(
            host=properties["notice_redis_host"],
            port=6379,
            db=int(properties["notice_redis_db"]),
            password=properties["notice_redis_pwd"]
        )

        # Read person info
        record = None
        while not record:
            print("read client info..")
            record = r.lpop(properties["user_info_redis_task_list"])
            if not record:
                time.sleep(3)
                continue

        person_info = json.loads(record)
        person_info["name"] = person_info["name"] + "XXXYYYZZZ"  # Prevent duplicate names
        person = person_info

        while True:
            print(f"Reading account.. {datetime.now().strftime(formatter)}")

            # Get registered account
            registered_account = None
            while not registered_account:
                registered_account = r.lpop(registered_account_list)
                if not registered_account:
                    print(f"can not find registered_account account [{registered_account_list}]")
                    time.sleep(3)
                    continue

            r.rpush(register_request_signal, "1")

            account_info = json.loads(registered_account)
            email = account_info["email"]
            email_pwd = account_info["email_pwd"]
            password = account_info["password"]

            # Mark as checking
            r.set(f"{email}_checking_visas", registered_account)

            client = MexicoClient(email, password, person, properties)

            # Login
            error_code1 = -1
            while True:
                error_code1 = client.login_with_recaptcha_with_error_code()
                if error_code1 in [101, 102, 104, 105, 200]:
                    break
                time.sleep(3)

            if error_code1 in [101, 102, 104, 105]:
                r.delete(f"{email}_checking_visas")
                time.sleep(1)
                continue

            verify_response = client.verify_user()
            if verify_response.get("success", False) is False:
                print(f"verifyResponse: {verify_response}")
                r.delete(f"{email}_checking_visas")
                continue

            check_count = 0
            max_check_count = 45

            while True:
                r.ping()
                check_count += 1

                if check_count >= max_check_count:
                    print("arrive max check count, change account!")
                    break

                error_code2 = -1
                if check_count % reset_num == 0:
                    while True:
                        error_code2 = client.login_with_recaptcha_with_error_code()
                        if error_code2 in [101, 102, 104, 105, 200]:
                            break
                        time.sleep(3)

                    if error_code2 in [101, 102, 104, 105]:
                        break

                    verify_response = client.verify_user()
                    if verify_response.get("success", False) is False:
                        print(f"verifyResponse: {verify_response}")
                        r.delete(f"{email}_checking_visas")
                        break

                check_code = client.checkVisasWithAuthByErrorCode(
                    client.person["dstOffice"]["cat_office_id"],
                    "main",
                    check_count
                )
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
                    print("don't sleep, next try!")
                elif check_code == 0:
                    if (check_count + 1) % reset_num != 0:
                        time.sleep(sleep_time)
                elif check_code == 1:
                    print("Found visas[sin][con]!!")
                    error_code = client.check_save_data1(r, "check_save_data")
                    if error_code == 1:
                        print("find save_data_right!")
                        office_var = client.person["dstOffice"]["var_cad_oficina"]
                        r.rpush(f"{office_var}_check_visas_sin_real", "find save_data")
                        r.rpush(f"{office_var}_check_visas_con_real", "find save_data")
                        r.rpush(f"{office_var}_check_visas_sin", "find save_data")
                        r.rpush(f"{office_var}_check_visas_con", "find save_data")
                        client.sendEmail(
                            "墨西哥放号 save_data",
                            f"{client.person['dstOffice']['cat_office_id']} 墨西哥放号了，快去抢吧[sin][con]!"
                        )
                elif check_code == 2:
                    print("Found visas[sin]!!")
                    error_code = client.check_save_data1(r, "check_save_data")
                    if error_code == 1:
                        print("find save_data_right!")
                        office_var = client.person["dstOffice"]["var_cad_oficina"]
                        r.rpush(f"{office_var}_check_visas_sin_real", "find save_data")
                        r.rpush(f"{office_var}_check_visas_sin", "find save_data")
                        client.sendEmail(
                            "墨西哥放号 save_data",
                            f"{client.person['dstOffice']['cat_office_id']} 墨西哥放号了，快去抢吧[sin]!"
                        )
                elif check_code == 3:
                    print("Found visas[con]!!")
                    error_code = client.check_save_data1(r, "check_save_data")
                    if error_code == 1:
                        print("find save_data_right!")
                        office_var = client.person["dstOffice"]["var_cad_oficina"]
                        r.rpush(f"{office_var}_check_visas_con_real", "find save_data")
                        r.rpush(f"{office_var}_check_visas_con", "find save_data")
                        client.sendEmail(
                            "墨西哥放号 save_data",
                            f"{client.person['dstOffice']['cat_office_id']} 墨西哥放号了，快去抢吧[con]!"
                        )

            r.rpush(used_account, registered_account)
            r.delete(f"{email}_checking_visas")

    @staticmethod
    def register_and_read_eyj_together_hotmail(args: List[str]):
        pattern = "book"  # or "check"

        # Connect to Redis
        r = redis.Redis(
            host='47.254.14.124',
            port=6379,
            db=0,
            password='2023@mexico'
        )

        # Set Redis keys based on pattern
        if pattern == "check":
            hotmail_account_raw = "0_raw_hotmail_account_check"
            register_request_signal = "0_register_request_signal_check_hotmail"
            account_need_activate = "0_account_need_activate_check_hotmail"
            registered_account_list = "0_registered_account_list_check"
        else:
            hotmail_account_raw = "0_raw_hotmail_account_book"
            register_request_signal = "0_register_request_signal_book_hotmail"
            account_need_activate = "0_account_need_activate_book_hotmail"
            registered_account_list = "0_registered_account_list_book"

        while True:
            # Wait for register signal
            while True:
                register_signal = r.lpop(register_request_signal)
                if not register_signal:
                    print(f"check register request signal! [{register_request_signal}]")
                    time.sleep(3)
                else:
                    print("find register signal!!")
                    break

            # Process accounts
            while True:
                account_raw = r.lpop(hotmail_account_raw)
                if not account_raw:
                    print(f"Can not find gmail account! [{hotmail_account_raw}]")
                    time.sleep(3)
                    continue

                print(f"find gmail account: {account_raw}")
                account_info_raw = json.loads(account_raw)
                email = account_info_raw["email"]
                email_pwd = account_info_raw["email_pwd"]
                password = f"{email_pwd}1@Gmail"

                print(f"注册=={email}==")
                error_code = MexicoClient().register_with_err_code(
                    "TESTNAME", "TESTFIRST", email, password,
                    246, 329198, "@hotmail.com", "@hotmail"
                )

                if error_code == 2:
                    print("register failed, select new account!")
                    time.sleep(10)
                    continue

                # Get activation link from email
                eyj_and_token = Test.read_hotmail_link_local(email, email_pwd)
                if not eyj_and_token.get("eyj"):
                    print("Can not find eyj or failed to register, change account!")
                    continue

                print(f"激活=={email}==")
                if MexicoMain.motivate_gmail_by_eyJ_and_token(
                        eyj_and_token["eyj"],
                        eyj_and_token["token"]
                ):
                    registered_account = json.dumps({
                        "email": email,
                        "email_pwd": email_pwd,
                        "password": password
                    })
                    r.rpush(registered_account_list, registered_account)
                    break
                else:
                    print("Motivate failed, change account!")
                    continue

    @staticmethod
    def motivate_gmail_by_eyJ_and_token(eyj: str, token: str) -> bool:
        eyj = eyj[eyj.index("validate/") + 9:]
        try_count = 0

        while True:
            # Get recaptcha
            get_recaptcha_url = f"https://citasapi.sre.gob.mx/api/appointment/lang/get-captcha/{eyj}"
            headers = {
                "accept": "application/json",
                "x-sre-api-key": "i3sid7ZQVsp0BPPC8yrdWqby5XZiRcu9",
                # Add other headers from Java version
            }

            response = requests.get(get_recaptcha_url, headers=headers)
            try:
                # Decrypt response and get captcha image
                # This part needs the actual decryption implementation
                pic_data = json.loads(response.text)  # Simplified
                if pic_data.get("img") == "null":
                    print("img is empty!")
                    return False

                # Save and recognize captcha
                recaptcha_pic_path = "register_recaptcha.png"
                # Save image and recognize code
                code = "recognized_code"  # Replace with actual recognition

                data = {
                    "id": eyj,
                    "captcha": code,
                    "token": token
                }

                # Encrypt data
                user_info_enc = "encrypted_data"  # Replace with actual encryption

                validate_url = "https://citasapi.sre.gob.mx/api/appointment/v1/validate"
                response2 = requests.post(
                    validate_url,
                    headers=headers,
                    json={"encrypt": user_info_enc}
                )

                response_data = json.loads(response2.text)  # Simplified
                if response_data.get("success", False):
                    return True
                elif "El dominio de correo electr" in response2.text:
                    try_count += 1
                    print(f"response: {response2.text}")
                    print(f"try again! {try_count}")
                    time.sleep(1)
                    continue

            except Exception as e:
                print(f"Error: {e}")
                continue


class Test:
    @staticmethod
    def read_hotmail_link_local(email: str, email_pwd: str) -> Dict:
        # This would call a Python script to read the email
        # Similar to the Java version that calls a Python script
        result = subprocess.run(
            ["python3", "/root/Mexico/register/obtain_email_link_from_hotmail.py", email, email_pwd],
            capture_output=True,
            text=True
        )

        lines = result.stdout.splitlines()
        if len(lines) > 1:
            return {
                "eyj": lines[-2],
                "token": lines[-1]
            }
        return {}


if __name__ == "__main__":
    # Example usage
    # MexicoMain.book_with_registered_account("hotmail", "10:30")
    # MexicoMain.check_visas_and_save_data_with_account(["246", "30", "9", "hotmail"])
    MexicoMain.register_and_read_eyj_together_hotmail([])
    pass