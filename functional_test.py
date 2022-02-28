import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class LoginTests(unittest.TestCase):

    def setUp(self):
        options = Options()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

    def test_login_successful(self):
        driver = self.driver
        driver.get("https://instaclone.yassbk.com/")

        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.form-container')))

        username_input = driver.find_element_by_css_selector('input[type="text"]')
        password_input = driver.find_element_by_css_selector('input[type="password"]')

        username = "realmadrid"
        password = 'dodo'

        username_input.send_keys(username)
        password_input.send_keys(password)

        driver.execute_script("""document.querySelector('button[type="submit"]').click()""")

        waiting_for_login = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.home-container')))

        assert waiting_for_login

    def test_login_fail(self):
        driver = self.driver
        driver.get("https://instaclone.yassbk.com/")

        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.form-container')))

        username_input = driver.find_element_by_css_selector('input[type="text"]')
        password_input = driver.find_element_by_css_selector('input[type="password"]')

        username = "homers"
        password = 'wrongPassword'

        username_input.send_keys(username)
        password_input.send_keys(password)

        driver.execute_script("""document.querySelector('button[type="submit"]').click()""")

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            assert True
        except:
            assert False

    def tearDown(self):
        self.driver.close()


if __name__ == "__main__":
    unittest.main()
