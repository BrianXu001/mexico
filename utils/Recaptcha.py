import subprocess
from typing import List


class Recaptcha:
    # TODO: Modify to server path
    py_script = "/root/Mexico/get_tickets/test.py"

    @staticmethod
    def recognize(file_name: str) -> str:
        try:
            process = subprocess.Popen(
                ["python3", Recaptcha.py_script, file_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate()

            if stderr:
                print(f"recaptcha error: {stderr}")
                return None

            if stdout:
                lines = stdout.splitlines()
                if lines:
                    return lines[-1].lower()

            return None

        except Exception as e:
            print(f"recognize runtime error: {e}")
            return None