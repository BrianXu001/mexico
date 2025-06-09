import os
import hashlib
from datetime import datetime, date
from typing import Optional
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import configparser

import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


class Utils:
    @staticmethod
    def crypto_js_encrypt(text: str, key: str) -> str:
        try:
            salt = get_random_bytes(8)
            key_iv = Utils.generate_key_and_iv(32, 16, 1, salt, key.encode('utf-8'), hashlib.md5)
            cipher = AES.new(key_iv[0], AES.MODE_CBC, key_iv[1])
            padded_text = pad(text.encode('utf-8'), AES.block_size)
            encrypted = cipher.encrypt(padded_text)
            prefix = b'Salted__' + salt
            return base64.b64encode(prefix + encrypted).decode('utf-8')
        except Exception as e:
            print(f"crypto_js_encrypt error: {e}")
            return ""

    @staticmethod
    def crypto_js_decrypt(str_to_dec, key):
        if not str_to_dec:
            return ""

        try:
            # Decode base64
            to_decrypt = base64.b64decode(str_to_dec)

            # Extract salt (bytes 8-16)
            salt = to_decrypt[8:16]

            # Generate key and IV
            key_and_iv = Utils.generate_key_and_iv(32, 16, 1, salt, key.encode('utf-8'), hashlib.md5)

            # Extract ciphertext (after first 16 bytes)
            ciphertext = to_decrypt[16:]

            # Create cipher and decrypt
            cipher = AES.new(key_and_iv[0], AES.MODE_CBC, iv=key_and_iv[1])
            decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size, style='pkcs7')

            return decrypted_data.decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {e}")
            return ""

    @staticmethod
    def generate_key_and_iv(key_length, iv_length, iterations, salt, password, hash_func):
        digest_length = hash_func().digest_size
        required_length = (key_length + iv_length + digest_length - 1) // digest_length * digest_length
        generated_data = bytearray(required_length)
        generated_length = 0

        try:
            # Repeat process until sufficient data has been generated
            while generated_length < key_length + iv_length:
                md = hash_func()

                # Digest data (last digest if available, password data, salt if available)
                if generated_length > 0:
                    md.update(generated_data[generated_length - digest_length:generated_length])
                md.update(password)
                if salt:
                    md.update(salt[:8])
                digest = md.digest()

                # Copy digest to generated data
                generated_data[generated_length:generated_length + len(digest)] = digest
                generated_length += len(digest)

                # Additional rounds
                for i in range(1, iterations):
                    md = hash_func()
                    md.update(generated_data[generated_length - digest_length:generated_length])
                    digest = md.digest()
                    generated_data[generated_length:generated_length + len(digest)] = digest

            # Copy key and IV into separate byte arrays
            result = [
                generated_data[:key_length],
                generated_data[key_length:key_length + iv_length] if iv_length > 0 else None
            ]

            return result
        finally:
            # Clean out temporary data
            for i in range(len(generated_data)):
                generated_data[i] = 0

    @staticmethod
    def send_email(subject, text):
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Sending Email...")
        from_address = "519335189@qq.com"
        username = "519335189@qq.com"
        password = "svcjgppiolmfcahc"
        # to_address = "519335189@qq.com"
        # to_address = "1219953432@qq.com"
        to_address = "519335189@qq.com"
        # Create message
        msg = MIMEText(text)
        msg['Subject'] = subject
        msg['From'] = from_address
        msg['To'] = to_address
        # msg['Date'] = formatdate(localtime=True)

        try:
            with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
                server.login(username, password)
                server.sendmail(from_address, [to_address], msg.as_string())
        except smtplib.SMTPResponseException as e:
            if e.smtp_code == -1 and e.smtp_error == b'\x00\x00\x00':
                print("Warning: Non-standard server response, but email was likely sent.")
            else:
                raise  # 重新抛出其他SMTP错误
        except Exception as e:
            print(f"Error: {e}")

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Send Email Success!")


if __name__ == "__main__":
    # encrypt_data = "U2FsdGVkX1+y5MVbkylIrKHtomhd65omeKM4t4DA9GblajwVTS8JdKER8hlmtwei9cK8YM8hZTk82aGt0p2J8osxVhc2f2kHKD5oPUWtj99VE3dc7Cj341M7AmFo+ACXLeyqWzTA+R2d1RBa1yjYiQ=="
    # res = Utils.crypto_js_decrypt(encrypt_data, "ef93be283631ae59456994273215fa5b")
    # print(res)
    Utils.send_email("Test", "test")
