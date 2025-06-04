import json
import time
import redis
from datetime import datetime
from typing import List, Dict


class Test:
    def read_hotmail_link_local(self, email: str, email_pwd: str) -> Dict:
        formatter = "%Y-%m-%d %H:%M:%S:%f"
        eyj = ""
        token = ""
        try_count_max = 2  # Allowing one retry
        try_count = 0

        while True:
            if try_count >= try_count_max:
                print("reach max try!")
                break

            try_count += 1
            data = self.get_eyJ_and_token_from_hotmail(email, email_pwd)
            print(f"data: {data}")

            if not data or (data.get("eyj") and not data["eyj"]):
                print("eyJ is empty, try again!")
                time.sleep(3)
            else:
                eyj = data["eyj"]
                token = data["token"]
                break

        eyj_and_token = {
            "eyj": eyj,
            "token": token
        }

        print(f"{datetime.now().strftime(formatter)} end!")
        return eyj_and_token

    def write_raw_gmail_to_redis(self):
        file_path = "/Users/xiaosongxu/all_work/project/code/java/travelagent/src/main/resources/gmail_2025_0424"

        # These would need to be implemented
        username_list = self.read_account(file_path)
        password_list = self.read_password(file_path)
        sec_email_list = self.read_sec_email(file_path)

        # Connect to Redis
        r = redis.Redis(
            host='47.254.14.124',
            port=6379,
            db=0,
            password='2023@mexico'
        )
        # gmail_account_raw = "0_raw_gmail_account_check"
        gmail_account_raw = "0_raw_gmail_account_book"
        r.select(0)

        start = 90
        end = 100

        for i in range(start, end):
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f"))
            print(f"===count: {i}")

            email = username_list[i].lower()
            email_pwd = password_list[i]
            sec_email = sec_email_list[i]
            password = f"{email_pwd}1@Gmail"

            print(f"account: {email} {email_pwd}")
            account_data = {
                "email": email,
                "email_pwd": email_pwd,
                "sec_email": sec_email,
                "password": password
            }
            r.rpush(gmail_account_raw, json.dumps(account_data))

    def write_raw_hotmail_to_redis(self):
        file_path = "/Users/xiaosongxu/all_work/project/code/java/travelagent/src/main/resources/hotmail_2025_0424"

        # These would need to be implemented
        username_list = self.read_account(file_path)
        password_list = self.read_password(file_path)

        # Connect to Redis
        r = redis.Redis(
            host='47.254.14.124',
            port=6379,
            db=0,
            password='2023@mexico'
        )

        # hotmail_account_raw = "0_raw_hotmail_account_check"
        hotmail_account_raw = "0_raw_hotmail_account_book"
        r.select(0)

        start = 750
        end = 751

        for i in range(start, end):
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f"))
            print(f"===count: {i}")

            email = username_list[i].lower()
            email_pwd = password_list[i]

            print(f"account: {email} {email_pwd}")
            account_data = {
                "email": email,
                "email_pwd": email_pwd
            }
            r.rpush(hotmail_account_raw, json.dumps(account_data))

    def read_account(self, file_path):
        user_list = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    spl = line.split("----")
                    if spl:  # Make sure there's at least one element
                        user_list.append(spl[0])
        except IOError as e:
            print(f"Error reading file: {e}")

        print(f"count: {len(user_list)}")
        return user_list

    def read_password(self, file_path):
        password_list = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                    parts = line.split("----")
                    if len(parts) > 1:  # Ensure there's at least two parts
                        password_list.append(parts[1])
        except IOError as e:
            print(f"Error reading file: {e}")

        print(f"count: {len(password_list)}")
        return password_list

    def read_sec_email(self, file_path):
        sec_email_list = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                    parts = line.split("----")
                    if len(parts) > 2:  # Ensure there's at least three parts
                        sec_email_list.append(parts[2])
        except IOError as e:
            print(f"Error reading file: {e}")

        print(f"count: {len(sec_email_list)}")
        return sec_email_list

    def write_possible_time_to_redis(self):
        # Configure Redis database
        r = redis.Redis(
            host='47.254.14.124',
            port=6379,
            db=0,
            password='2023@mexico',
            decode_responses=True
        )

        # Select office region
        # office_state = "GUANGZHOU"
        # office_state = "SHANGHAI"
        # office_state = "BEIJING"
        # office_state = "AUSTRIA"
        # office_state = "CANBERRA"
        office_state = "RIO DE JANEIRO"

        possible_day = []
        # possible_day.extend(["2023-10-30", "2023-10-31"])
        # possible_day.extend(["2024-10-08", "2024-10-09", "2024-10-10", "2024-10-11"])

        possible_day.extend([
            "2025-06-03", "2025-06-04", "2025-06-05", "2025-06-06",
            "2025-06-09", "2025-06-10", "2025-06-11", "2025-06-12", "2025-06-13",
            "2025-06-16", "2025-06-17", "2025-06-18", "2025-06-19", "2025-06-20",
            "2025-06-23", "2025-06-24", "2025-06-25", "2025-06-26", "2025-06-27",
            "2025-06-30"
        ])

        # possible_day.extend(["2025-04-02", "2025-04-03"])
        # possible_day.extend(["2025-04-07", "2025-04-08", "2025-04-09", "2025-04-10", "2025-04-11"])
        # possible_day.extend(["2025-04-14", "2025-04-15", "2025-04-16", "2025-04-17", "2025-04-18"])
        # possible_day.extend(["2025-04-21", "2025-04-22", "2025-04-23", "2025-04-24", "2025-04-25"])
        # possible_day.extend(["2025-04-28", "2025-04-29", "2025-04-30"])
        # possible_day.extend(["2025-02-11", "2025-02-12"])
        # possible_day.extend(["2024-10-21", "2024-10-22", "2024-10-23", "2024-10-24", "2024-10-25"])
        # possible_day.extend(["2024-10-28", "2024-10-29", "2024-10-30"])

        # Shanghai
        possible_time_sin_sh = [["08:45:00", "09:00:00"]]  # sin
        possible_time_con_sh = [["08:45:00", "09:00:00"]]  # con

        # Guangzhou
        possible_time_sin_gz = [["09:30:00", "09:45:00"]]  # sin
        possible_time_con_gz = [["10:00:00", "10:15:00"]]  # con

        # Beijing
        possible_time_sin_bj = [
            ["10:45:00", "11:00:00"],
            ["11:00:00", "11:15:00"],
            ["11:15:00", "11:30:00"]
        ]
        possible_time_con_bj = [
            ["10:45:00", "11:00:00"],
            ["11:00:00", "11:15:00"],
            ["11:15:00", "11:30:00"]
        ]

        # Austria
        possible_time_sin_aus = [["09:45:00", "10:00:00"]]

        # Australia
        possible_time_sin_austrlian = [["09:00:00", "10:00:00"]]

        # Brazil
        possible_time_sin_brazil = [
            ["09:45:00", "10:00:00"],
            ["11:00:00", "11:15:00"]
        ]
        possible_time_con_brazil = [
            ["09:00:00", "09:15:00"],
            ["09:15:00", "09:30:00"]
        ]

        # Initialize variables based on office state
        possible_sin_time = []
        possible_con_time = []
        possible_times_sin_list = ""
        possible_times_con_list = ""

        if office_state == "SHANGHAI":
            possible_sin_time = possible_time_sin_sh
            possible_con_time = possible_time_con_sh
            possible_times_sin_list = "SHANGHAI_possible_sin_times"
            possible_times_con_list = "SHANGHAI_possible_con_times"
        elif office_state == "GUANGZHOU":
            possible_sin_time = possible_time_sin_gz
            possible_con_time = possible_time_con_gz
            possible_times_sin_list = "GUANGZHOU_possible_sin_times"
            possible_times_con_list = "GUANGZHOU_possible_con_times"
        elif office_state == "BEIJING":
            possible_sin_time = possible_time_sin_bj
            possible_con_time = possible_time_con_bj
            possible_times_sin_list = "BEIJING_possible_sin_times"
            possible_times_con_list = "BEIJING_possible_con_times"
        elif office_state == "AUSTRIA":
            possible_sin_time = possible_time_sin_aus
            possible_times_sin_list = "AUSTRIA_possible_sin_times"
        elif office_state == "CANBERRA":
            possible_sin_time = possible_time_sin_austrlian
            possible_times_sin_list = "CANBERRA_possible_sin_times"
        elif office_state == "RIO DE JANEIRO":
            possible_sin_time = possible_time_sin_brazil
            possible_con_time = possible_time_con_brazil
            possible_times_sin_list = "RIO DE JANEIRO_possible_sin_times"
            possible_times_con_list = "RIO DE JANEIRO_possible_con_times"

        print("==The data in the sin list==>")
        last_list_sin = r.lrange(possible_times_sin_list, 0, -1)
        for time in last_list_sin:
            print(time)

        print("==The data in the con list==>")
        last_list_con = r.lrange(possible_times_con_list, 0, -1)
        for time in last_list_con:
            print(time)

        print("==drop the list==")
        r.ltrim(possible_times_sin_list, 1, 0)  # This empties the list
        r.ltrim(possible_times_con_list, 1, 0)  # This empties the list

        for day in possible_day:
            for time in possible_sin_time:
                day_str = {
                    "date": day,
                    "initialTime": time[0],
                    "endTime": time[1],
                    "cat_procedure_id": 31,
                    "cat_procedure_type_id": 10,
                    "cat_procedure_subtype_id": None,
                    "total_by_block": 1,
                    "availables_by_block": 1
                }
                r.lpush(possible_times_sin_list, json.dumps(day_str))

        for day in possible_day:
            for time in possible_con_time:
                day_str = {
                    "date": day,
                    "initialTime": time[0],
                    "endTime": time[1],
                    "cat_procedure_id": 31,
                    "cat_procedure_type_id": 10,
                    "cat_procedure_subtype_id": None,
                    "total_by_block": 1,
                    "availables_by_block": 1
                }
                r.lpush(possible_times_con_list, json.dumps(day_str))

        print("==The data write in to the sin list==>")
        lists_sin = r.lrange(possible_times_sin_list, 0, -1)
        for time in lists_sin:
            time_obj = json.loads(time)
            print(time_obj)

        print("==The data write in to the con list==>")
        lists_con = r.lrange(possible_times_con_list, 0, -1)
        for time in lists_con:
            time_obj = json.loads(time)
            print(time_obj)


if __name__ == "__main__":

    t1 = Test()
    # t1.write_possible_time_to_redis()
    # t1.write_raw_gmail_to_redis()
    t1.write_raw_hotmail_to_redis()