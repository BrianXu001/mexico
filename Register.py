import json
import time
from datetime import datetime
import redis
import base64
import random
import requests

from utils.Utils import Utils
from utils.Recaptcha import Recaptcha
from utils.HttpUtils import HttpUtils
from utils import obtain_email_link_from_hotmail

import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import argparse

print("install ChromeDriverManager")
ChromeDriverManager().install()
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


class Register:
    def __init__(self, register_type="check", email_type="hotmail"):
        self.key = "ca0d02b0df9839e77ae6ad1c1b48654c"
        self.register_type = register_type
        self.email_type = email_type

        self.redis_signal_list = "0_"
        self.redis_account_raw_list = "0_"
        self.redis_registered_account_list = "0_"
        # check or book
        if self.register_type == "book":
            self.redis_signal_list += "_book"
            self.redis_account_raw_list += "_book"
            self.redis_registered_account_list += "_book"
        else:
            self.redis_signal_list += "_check"
            self.redis_account_raw_list += "_check"
            self.redis_registered_account_list += "_check"
        # hotmail or gmail
        if self.email_type == "gmail":
            self.redis_signal_list += "_gmail"
            self.redis_account_raw_list += "_gmail"
        else:
            self.redis_signal_list += "_hotmail"
            self.redis_account_raw_list += "_hotmail"
        self.redis_signal_list += "_register_signal"
        self.redis_account_raw_list += "_raw_account"
        self.redis_registered_account_list += "_registered_account"


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

    def get_register_params(self, name, first_name, email, password, office_id, state_id, domain, word_key, captcha):
        # Generate random phone number
        heads = ["181", "189", "139", "186", "132"]
        number = random.choice(heads) + " "
        number += "".join([str(random.randint(0, 9)) for _ in range(4)]) + " "
        number += "".join([str(random.randint(0, 9)) for _ in range(4)])

        # Create the user info dictionary
        user_info = {
            "name": name,
            "firstName": first_name,
            "lastName": "",
            "cellPhone": number,
            "homePhone": "",
            "email": email,
            "dominio": domain,
            "password": password,
            "recaptchaVerified": False,
            "GrecaptchaResponse": None,
            "typeAppointment": "1",
            "cat_country_id": 44,
            "cat_nationality_id": 44,
            "cat_office_id": office_id,
            "cat_state_id": state_id,
            "langDefault": "es",
            "captcha": captcha,
            "wordKey": word_key,
            "cat_paises_id": 44,
            "password_confirmation": password,
            "cellPhoneFormatInternational": f"+86 {number}",
            "view_info_complete": False
        }

        return user_info

    # Example usage:
    # params = get_register_params("XIAOYAN", "LI", "sdfjkj@hotmail.com", "abcD1@Hotmail",
    #                             246, 329198, "@hotmail.com", "@hotmail", "puqmmr")
    # print(json.dumps(params, indent=2))

    def register_with_err_code(self, name, firstName, email, password, officeId, stateId, domain, wordKey):
        url = "https://citasapi.sre.gob.mx/api/appointment/v1/register"

        headers = {
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
            "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-csrf-token": "",
            "x-requested-with": "XMLHttpRequest",
            "x-sre-api-key": "i3sid7ZQVsp0BPPC8yrdWqby5XZiRcu9"
        }

        params = {}
        try_count = 0

        while True:
            try:
                recaptcha_code = self.get_recaptcha_code(email)
                print(datetime.now(), f"recaptcha_code:{recaptcha_code}")
                if not recaptcha_code:
                    time.sleep(5)
                    continue

                requestInfo = self.get_register_params(name, firstName, email, password, officeId,
                                                     stateId, domain, wordKey, recaptcha_code)
                print(f"requestInfo:{requestInfo}")

                requestInfoEncrypt = Utils.crypto_js_encrypt(json.dumps(requestInfo), self.key)
                params["encrypt"] = requestInfoEncrypt

                # response = self.http_utils.do_post(url, headers, json.dumps(params))
                response = requests.post(
                    url,
                    headers=headers,
                    json=params
                )
                responseContent = response.content
                print(f"responseContent:{responseContent}")

                decryptedContent = Utils.crypto_js_decrypt(responseContent, self.key)

                if not decryptedContent:
                    print("response is empty!")
                elif "Captcha ERROR" in decryptedContent:
                    print(f"{name} response:{decryptedContent}")
                    time.sleep(3)
                    continue
                elif "No fue posible guardar la informaci" in decryptedContent:
                    print(f"{name} response:{decryptedContent}")
                    return 1
                elif "El dominio de correo electr" in decryptedContent:
                    try_count += 1
                    print(f"{name} response:{decryptedContent}")
                    print(f"try again! {try_count}")
                    time.sleep(3)
                    continue
                else:
                    print(f"{name} response:{decryptedContent}")
                    break

            except Exception as e:
                print("==register error==>")
                import traceback
                traceback.print_exc()
                return 2

        return 0

    def check_citas_homepage(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--password-store=basic")  # 禁用密钥环
        chrome_options.add_argument("--no-first-run")
        driver = uc.Chrome(options=chrome_options, verify=False)

        while True:
            driver.get("https://citas.sre.gob.mx/")
            driver.maximize_window()
            try:
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

    def register(self, username, password):
        firstNameCandidates = [
            "ZHAO", "QIAN", "SUN", "LI", "ZHOU", "WU",
            "ZHENG", "WANG", "XU", "XIONG", "JIANG", "MIN", "CAI"
        ]
        nameCandidates1 = [
            "ZI", "XIAO", "QIAO", "MING", "HUA", "GUAN",
            "HAN", "JIAN", "WEI", "YU", "XIANG", "HENG", "QI"
        ]
        nameCandidates2 = [
            "YANG", "SHAN", "YUAN", "SONG", "CHANG", "KAI",
            "RUI", "SHI", "YONG", "YI", "ZHONG", "HUANG"
        ]
        firstName = random.choice(firstNameCandidates)
        name = random.choice(nameCandidates1) + random.choice(nameCandidates2)

        domain = username[username.index("@"):]
        wordKey = domain[:domain.index(".")]
        print("domain:" + domain)
        print("wordKey:" + wordKey)

        # guangzhou
        officeId = 246
        stateId = 329198
        # shanghai
        # officeId = 164
        # stateId = 3667
        # beijing
        # officeId = 59
        # stateId = 3643
        # TODO 首先访问主页
        print("check_citas_homepage")
        self.check_citas_homepage()
        return self.register_with_err_code(name, firstName, username, password, officeId, stateId, domain, wordKey)

    def motivate_by_eyj_and_token(self, eyJ, token, max_retries=99):
        eyJ = eyJ[eyJ.index("validate/") + 9:]
        try_count = 0

        headers = {
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
            "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-csrf-token": "",
            "x-requested-with": "XMLHttpRequest",
            "x-sre-api-key": "i3sid7ZQVsp0BPPC8yrdWqby5XZiRcu9"
        }

        while try_count < max_retries:
            try:
                # Step 1: Get captcha image
                get_recaptcha_url = f"https://citasapi.sre.gob.mx/api/appointment/lang/get-captcha/{eyJ}"
                response = requests.get(get_recaptcha_url, headers=headers)

                if response.status_code != 200:
                    print("Failed to get captcha")
                    try_count += 1
                    time.sleep(1)
                    continue
                try:
                    content = response.text
                    decrypted_content = Utils.crypto_js_decrypt(content, self.key)
                    data = json.loads(decrypted_content)
                    img_data = data.get("img", "")[22:]  # Remove the data:image/png;base64, prefix
                    code = Recaptcha.recognize(img_data)
                    print(f"recognize code: {code}")

                except Exception as e:
                    print("generate_recaptcha_pic error!")
                    print(e)
                    try_count += 1
                    time.sleep(1)
                    continue

                # Step 2: Validate captcha
                validate_url = "https://citasapi.sre.gob.mx/api/appointment/v1/validate"
                data = {
                    "id": eyJ,
                    "captcha": code,
                    "token": token
                }

                # Assuming encryption is needed (placeholder)
                # In Python, you would need to implement the encryption logic
                encrypted_data = Utils.crypto_js_encrypt(json.dumps(data), self.key)  # You need to implement this
                params = {"encrypt": encrypted_data}

                # Make the validation request
                response2 = requests.post(validate_url, headers=headers, json=params)

                if response2.status_code != 200:
                    print("Validation request failed")
                    try_count += 1
                    time.sleep(1)
                    continue

                try:
                    response_str = Utils.crypto_js_decrypt(response2.text, self.key)  # You need to implement this
                    response_json = json.loads(response_str)
                    print(response_str)
                    if response_json.get("success", False):
                        return True
                    elif "El dominio de correo electr" in response_str:
                        try_count += 1
                        print(f"response: {response_str}")
                        print(f"try again! {try_count}")
                        time.sleep(1)
                        continue

                except Exception as e:
                    print("Error processing validation response")
                    print(e)
                    try_count += 1
                    time.sleep(1)
                    continue

            except Exception as e:
                print("Unexpected error in main loop")
                print(e)
                try_count += 1
                time.sleep(1)

        return False

    def register_and_read_eyj_together_hotmail(self):
        # Connect to Redis
        redis_conn = redis.Redis(host='47.254.14.124', port=6379, db=0, password='2023@mexico', decode_responses=True)
        while True:
            # Wait for register signal
            while True:
                register_signal = redis_conn.lpop(self.redis_signal_list)
                if not register_signal:
                    print(f"check register request signal![{self.redis_signal_list}]")
                    time.sleep(3)
                else:
                    print("find register signal!!")
                    break

            # Process accounts
            while True:
                account_raw = redis_conn.lpop(self.redis_account_raw_list)
                if not account_raw:
                    print(f"Can not find gmail account![{self.redis_account_raw_list}]")
                    time.sleep(3)
                    continue

                print(f"find gmail account:{account_raw}")
                account_info_raw = json.loads(account_raw)
                email = account_info_raw["email"]
                email_pwd = account_info_raw["email_pwd"]
                password = email_pwd + "1@Gmail"

                # Register
                print(f"注册=={email}==" + datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3])
                error_code = self.register(email, password)
                if error_code == 2:
                    print("register failed, select new account!")
                    time.sleep(10)
                    continue

                # Read EYJ from browser
                try_count = 0
                eyj_and_token = "", ""
                while try_count < 2:
                    try_count += 1
                    eyj_and_token = obtain_email_link_from_hotmail.obtain_email_link(email, email_pwd)
                    print("eyj_and_token", eyj_and_token)
                    if eyj_and_token[0]:
                        break
                if not eyj_and_token[0]:
                    print("Can not find eyj or failed to register, change account!")
                    continue

                eyj_url_motivate = eyj_and_token[0]
                token = eyj_and_token[1]

                print(f"激活=={email}==" + datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3])
                if self.motivate_by_eyj_and_token(eyj_url_motivate, token):
                    # Write to Redis
                    registered_account = json.dumps({
                        "email": email,
                        "email_pwd": email_pwd,
                        "password": password
                    })
                    redis_conn.rpush(self.redis_registered_account_list, registered_account)
                    break
                else:
                    print("Motivate failed, change account!")
                    continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="输入gmail账号、密码")
    parser.add_argument("arg1", help="register_type")
    parser.add_argument("arg2", help="email_type")
    args = parser.parse_args()
    register_type = args.arg1
    email_type = args.arg2
    register = Register(register_type, email_type)
    register.register_and_read_eyj_together_hotmail()