import os
import hashlib
from datetime import datetime, date
from typing import Optional
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import configparser


class Utils:

    @staticmethod
    def write_file_from_stream(filename: str, stream) -> None:
        if not filename or not stream:
            return

        try:
            with open(filename, 'wb') as f:
                for chunk in stream.iter_content(4096):
                    if chunk:
                        f.write(chunk)
        except Exception as e:
            print(f"write_file_from_stream error: {e}")

    @staticmethod
    def write_file_from_string(filename: str, content: str) -> None:
        if not filename:
            filename = "tmp.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"write_file_from_string error: {e}")

    @staticmethod
    def get_string_from_stream(stream) -> str:
        try:
            return stream.read().decode('utf-8')
        except Exception as e:
            print(f"get_string_from_stream error: {e}")
            return ""

    @staticmethod
    def get_db_config() -> dict:
        config = configparser.ConfigParser()
        try:
            config.read('config/dbconfig.ini')
            return {section: dict(config.items(section)) for section in config.sections()}
        except Exception as e:
            print(f"get_db_config error: {e}")
            return {}

    @staticmethod
    def crypto_js_encrypt(text: str, key: str) -> str:
        try:
            salt = get_random_bytes(8)
            key_iv = Utils._generate_key_and_iv(32, 16, 1, salt, key.encode('utf-8'), hashlib.md5)
            cipher = AES.new(key_iv[0], AES.MODE_CBC, key_iv[1])
            padded_text = pad(text.encode('utf-8'), AES.block_size)
            encrypted = cipher.encrypt(padded_text)
            prefix = b'Salted__' + salt
            return base64.b64encode(prefix + encrypted).decode('utf-8')
        except Exception as e:
            print(f"crypto_js_encrypt error: {e}")
            return ""

    @staticmethod
    def crypto_js_decrypt(encrypted: str, key: str) -> str:
        try:
            if not encrypted:
                return ""

            decoded = base64.b64decode(encrypted)
            salt = decoded[8:16]
            encrypted_data = decoded[16:]
            key_iv = Utils._generate_key_and_iv(32, 16, 1, salt, key.encode('utf-8'), hashlib.md5)
            cipher = AES.new(key_iv[0], AES.MODE_CBC, key_iv[1])
            decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"crypto_js_decrypt error: {e}")
            return ""

    @staticmethod
    def _generate_key_and_iv(key_length, iv_length, iterations, salt, password, hash_func):
        digest = b''
        data = salt + password

        for i in range(iterations):
            data = hash_func(data).digest()
            digest += data

        key = digest[:key_length]
        iv = digest[key_length:key_length + iv_length]

        return (key, iv)

    @staticmethod
    def get_age(birth_date: str) -> int:
        try:
            birth = datetime.strptime(birth_date, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            return age
        except Exception as e:
            print(f"get_age error: {e}")
            return 25

    @staticmethod
    def convert_base64_to_image(base64_str: str, output_path: str) -> None:
        try:
            if not base64_str or not output_path:
                return

            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(base64_str))
        except Exception as e:
            print(f"convert_base64_to_image error: {e}")