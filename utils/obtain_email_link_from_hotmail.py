from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException, StaleElementReferenceException

import undetected_chromedriver as uc

# from selenium import webdriver

import time, traceback
import argparse

#ChromeDriverManager().install()
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


def obtain_email_link(email, password):
    # chrome_options = Options()
    # # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--password-store=basic")  # 禁用密钥环
    # chrome_options.add_argument("--no-first-run")
    # chrome_options.add_argument("--start-maximized")

    # chrome_version = webdriver.Chrome(options=chrome_options).capabilities['browserVersion']
    # print(f"Chrome 版本: {chrome_version}")

    # 检查 ChromeDriver 版本
    # driver_version = webdriver.Chrome(options=chrome_options).capabilities['chrome']['chromedriverVersion'].split(' ')[0]
    # print(f"ChromeDriver 版本: {driver_version}")

    email_title_cn = 'SRE 预约注册'
    email_title_en = 'Registro a Citas SRE'
    link_prefix = "https://citas.sre.gob.mx/register/validate/"
    # print("初始化chrome")
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--password-store=basic")  # 禁用密钥环
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--start-maximized")
    driver = uc.Chrome(options=chrome_options, verify=False)
    # driver = webdriver.Chrome(options=chrome_options)
    # 打开谷歌邮箱登录页面
    # driver.get("https://mail.google.com/mail/u/0/")
    print("open url")
    driver.get("https://outlook.office365.com")

    print("input email and password")
    try:
        try:
            login_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Sign in')]"))
            )
            login_link.click()
        except Exception as e:
            pass
            # print("Sign in按钮未能获取")
        # 等待电子邮件输入框可见
        # print("等待电子邮件输入框可见")
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.NAME, "loginfmt"))
        )
        # 输入电子邮件
        # print("输入电子邮件")
        email_input = driver.find_element(By.NAME, "loginfmt")
        email_input.send_keys(email)
        time.sleep(2)
        # 点击下一步
        email_input.send_keys(Keys.RETURN)
        # 等待密码输入框可见
        # print("等待密码输入框可见")
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.NAME, "passwd"))
        )

        # 输入密码
        # print("输入密码")
        password_input = driver.find_element(By.NAME, "passwd")
        password_input.send_keys(password)
        time.sleep(2)
        # 点击下一步或登录按钮
        # print("点击下一步或登录按钮")
        password_input.send_keys(Keys.RETURN)

        print("check account")
        count_try_max = 10
        count = 0
        while True:
            if count > count_try_max:
                break

            select_1 = driver.find_elements(By.XPATH, "//button[@aria-label='Skip for now' or @aria-label='暂时跳过']")
            select_2 = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='secondaryButton']")
            select_3 = driver.find_elements(By.CSS_SELECTOR, "svg.fui-Icon-regular")
            select_4 = driver.find_elements(By.ID, "declineButton")

            select_abuse = driver.find_elements(By.ID, "serviceAbuseLandingTitle")
            select_skip = driver.find_elements(By.ID, "iShowSkip")

            if (len(select_abuse) > 0):
                print("账号被锁定，获取link失败！")
                driver.quit()
                return "", ""
            elif (len(select_skip) > 0):
                try:
                    button = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.ID, "iShowSkip"))
                    )
                    button.click()
                    print("iShowSkip")
                except ElementClickInterceptedException as e:
                    time.sleep(1)
                    continue
                time.sleep(3)
                continue

            # print("============aaaaaaaaaaa==============")
            # skip for now 2
            if (len(select_1) > 0):
                # print("============3==============")
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[@aria-label='Skip for now' or @aria-label='暂时跳过']"))
                )
                button.click()
                print("Skip for now")
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "declineButton"))
                )
                button.click()
                print("declineButton")
                break
            elif (len(select_2) > 0):
                # print("============4==============")
                try:
                    button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='secondaryButton']"))
                    )
                    button.click()
                    print("secondaryButton")
                    time.sleep(5)
                    # print("============4-1==============")
                    select4 = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='secondaryButton']")
                    select5 = driver.find_elements(By.CSS_SELECTOR, "svg.fui-Icon-regular")
                    if (len(select4) > 0):
                        # print("============4-1-1==============")
                        button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='secondaryButton']"))
                        )
                        button.click()
                        print("secondaryButton")
                    elif (len(select5) > 0):
                        # print("============4-1-2==============")
                        close_icon = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "svg.fui-Icon-regular"))
                        )
                        close_icon.click()
                        print("svg.fui-Icon-regular")
                    # print("============4-2==============")
                except TimeoutException as e:
                    time.sleep(5 * 60)
                break
            elif (len(select_3) > 0):
                # print("============5==============")
                close_icon = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "svg.fui-Icon-regular"))
                )
                close_icon.click()
                print("svg.fui-Icon-regular")
                break
            elif (len(select_4) > 0):
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "declineButton"))
                )
                button.click()
                print("declineButton")
                break
            count += 1
            time.sleep(3)
        if count > count_try_max:
            driver.quit()
            print("count", count)
            return "", ""

        print("find email..")
        count = 0
        count_try_max = 10
        while True:
            if count > count_try_max:
                break
            select_1 = driver.find_elements(By.ID, "newSessionLink")
            select_2 = driver.find_elements(By.XPATH, f"//div[@data-folder-name='垃圾邮件' or @data-folder-name='junk email']")
            if (len(select_1) > 0):
                try:
                    button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "newSessionLink"))
                    )
                    button.click()
                    time.sleep(3)
                    print("find newSessionLink")
                except ElementClickInterceptedException as e:
                    time.sleep(1)
                    continue
                time.sleep(3)
                continue
            elif (len(select_2) > 0):
                print("find junk email")
                break
            else:
                time.sleep(3)
            count += 1
        if count > count_try_max:
            driver.quit()
            print("try_count:", count)
            return "", ""
        # 查找邮件
        print("search email..")
        while True:
            # 查找收件箱
            try:
                mail_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.XPATH, f"//div[@data-folder-name='收件箱' or @data-folder-name='inbox']")))
                mail_element.click()
                print("search inbox..")
            except ElementClickInterceptedException as e:
                try:
                    label_element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//span[span[span[contains(., '拒绝') or contains(., 'Reject') ]]]"))
                    )
                    label_element.click()
                    continue
                except TimeoutException as e:
                    pass
            except TimeoutException as e:
                pass

            try:
                mail_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.XPATH, f"//div[span[contains(., '{email_title_cn}') or contains(., '{email_title_en}')]]")))
                mail_element.click()
                break
            except ElementClickInterceptedException as e:
                try:
                    label_element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//span[span[span[contains(., '拒绝') or contains(., 'Reject') ]]]"))
                    )
                    label_element.click()
                    continue
                except TimeoutException as e:
                    pass
            except TimeoutException as e:
                pass
            # 查找垃圾箱
            try:
                mail_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.XPATH, f"//div[@data-folder-name='垃圾邮件' or @data-folder-name='junk email']")))
                mail_element.click()
                print("search junk email..")
            except ElementClickInterceptedException as e:
                try:
                    label_element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//span[span[span[contains(., '拒绝') or contains(., 'Reject') ]]]"))
                    )
                    label_element.click()
                    continue
                except Exception as e:
                    pass
                time.sleep(1)
                continue
            except TimeoutException as e:
                pass

            try:
                mail_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.XPATH, f"//div[span[contains(., '{email_title_cn}') or contains(., '{email_title_en}')]]")))
                mail_element.click()
                break
            except ElementClickInterceptedException as e:
                try:
                    label_element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//span[span[span[contains(., '拒绝') or contains(., 'Reject') ]]]"))
                    )
                    label_element.click()

                except TimeoutException as e:
                    pass
            except TimeoutException as e:
                pass
            break

        print("search hred and token")
        try:
            active_href = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '{link_prefix}')]")))
            active_href_value = active_href.get_attribute('href')
            print(active_href_value)

            element_token = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.XPATH, "//p[font[contains(text(), 'Token de validac')]]")))
            print(element_token.text)
            token = element_token.text[element_token.text.find(":") + 1:].strip()
            driver.quit()
            return active_href_value, token
        except StaleElementReferenceException as e:
            # 获取邮件内容时页面发生了变化
            time.sleep(1)
        except TimeoutException as e:
            pass

        driver.quit()
        print("got some error")
        return "", ""

    except Exception as e:
        driver.quit()
        traceback_info = traceback.format_exc()
        print("got exception:", f'{traceback_info}')
        return "", ""


if __name__ == "__main__":
#    parser = argparse.ArgumentParser(description="输入gmail账号、密码")
#    parser.add_argument("arg1", help="账号")
#    parser.add_argument("arg2", help="密码")
#    args = parser.parse_args()
#    email = args.arg1
#    password = args.arg2
    # bdovoug2@hotmail.com----qas340671
    email = "bdovoug2@hotmail.com"
    password = "qas340671"
    obtain_email_link(email, password)