import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class RubikaAuth:
    def __init__(self, profile_path='chrome_profile'):
        self.profile_path = os.path.abspath(profile_path)
        self.base_url = "https://m.rubika.ir/"
        
        if not os.path.exists(self.profile_path):
            os.makedirs(self.profile_path)
            
        self.driver = self._init_driver()

    def _init_driver(self):
        print("[System] Firing up Chrome...")
        opt = Options()
        opt.add_experimental_option("detach", True) 
        
        opt.add_experimental_option("excludeSwitches", ["enable-automation"])
        opt.add_argument("--disable-blink-features=AutomationControlled")
        
        opt.add_argument(f"--user-data-dir={self.profile_path}")
        opt.add_argument("--profile-directory=Default")
                
        # Selenium manager
        driver = webdriver.Chrome(options=opt)
        driver.maximize_window()
        return driver

    def login(self):
        self.driver.get(self.base_url)
        time.sleep(3)

        needs_login = self.driver.find_elements(By.XPATH, "//input[@type='tel' or @name='phone_number']")
        
        if "login" in self.driver.current_url or needs_login:
            print("==> Not logged in!")
            input("Tu browser login kon, chat ha ke load shod inja ENTER bezan... ")
            print("Session saved.")
        else:
            print("Already logged in. Profile works.")
            
        return self.driver