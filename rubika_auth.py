import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class RubikaAuth:
    def __init__(self, data_dir='chrome_profile'):
        # Chrome requires an absolute path for user data directories
        self.data_dir = os.path.abspath(data_dir)
        self.base_url = "https://m.rubika.ir/"
        
        # Ensure the data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.driver = self._initialize_driver()

    def _initialize_driver(self):
        """Sets up the driver using a persistent, native Chrome profile."""
        print("[System] Initializing Chrome WebDriver with Native Profile...")
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True) 
        
        # Stealth options to hide automation
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # THE MAGIC FIX: Tell Chrome to use a persistent local folder for ALL session data
        # This completely replaces our manual cookie/localStorage injection
        chrome_options.add_argument(f"--user-data-dir={self.data_dir}")
        chrome_options.add_argument("--profile-directory=Default")
                
        # Fallback mechanism: Check for a local driver in a 'drivers' folder
        local_driver_path = os.path.join(os.getcwd(), 'drivers', 'chromedriver.exe')
        
        try:
            if os.path.exists(local_driver_path):
                print(f"[System] Local driver found at {local_driver_path}. Bypassing network download.")
                service = Service(local_driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                print("[System] No local driver found. Attempting dynamic download via Selenium Manager...")
                driver = webdriver.Chrome(options=chrome_options)
                
            driver.maximize_window()
            return driver
            
        except Exception as e:
            print("\n[Error] Failed to initialize WebDriver. Ensure you have an active internet connection, or place 'chromedriver.exe' in the 'drivers' folder.")
            raise e

    def login(self):
        """Handles navigating to Rubika. Login state is now managed natively by Chrome."""
        print(f"[System] Navigating to {self.base_url}")
        self.driver.get(self.base_url)
        time.sleep(3)

        # Check if Rubika's login button or input field is present to determine if we need manual login
        # If the URL redirects to the messenger or vitrin, we are already logged in
        if "login" in self.driver.current_url or len(self.driver.find_elements(By.XPATH, "//input[@type='tel' or @name='phone_number']")) > 0:
            print("\n" + "="*50)
            print("[Action Required] You are not logged in.")
            print("1. Please log in manually in the opened browser window.")
            print("2. Enter the SMS verification code.")
            print("3. Wait until you fully see your chats.")
            print("="*50 + "\n")
            
            input("Press ENTER in this console *ONLY AFTER* you have successfully logged in...")
            print("[Success] Session saved automatically by Chrome.")
        else:
            print("[Success] Native Chrome Profile loaded. You are already logged in.")
            
        return self.driver