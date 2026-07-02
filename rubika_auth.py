import pickle
import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class RubikaAuth:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.cookie_path = os.path.join(self.data_dir, 'cookies.pkl')
        self.local_storage_path = os.path.join(self.data_dir, 'local_storage.json')
        self.base_url = "https://m.rubika.ir/"
        
        # Ensure the data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.driver = self._initialize_driver()

    def _initialize_driver(self):
        """Sets up the driver, prioritizing a bundled local driver for portability."""
        print("[System] Initializing Chrome WebDriver...")
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True) 
        
        # Fallback mechanism: Check for a local driver in a 'drivers' folder
        # This is what guarantees it runs on your professor's machine offline
        local_driver_path = os.path.join(os.getcwd(), 'drivers', 'chromedriver.exe')
        
        try:
            if os.path.exists(local_driver_path):
                print(f"[System] Local driver found at {local_driver_path}. Bypassing network download.")
                service = Service(local_driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # If no local driver, fallback to Selenium Manager (requires internet/VPN on first run)
                print("[System] No local driver found. Attempting dynamic download via Selenium Manager...")
                driver = webdriver.Chrome(options=chrome_options)
                
            driver.maximize_window()
            return driver
            
        except Exception as e:
            print("\n[Error] Failed to initialize WebDriver. Ensure you have an active internet connection, or place 'chromedriver.exe' in the 'drivers' folder.")
            raise e

    def login(self):
        """Handles navigating to Rubika and managing the session state."""
        print(f"[System] Navigating to {self.base_url}")
        self.driver.get(self.base_url)

        # Check that BOTH the cookies and local storage files exist
        if os.path.exists(self.cookie_path) and os.path.exists(self.local_storage_path):
            print("[System] Found saved session data. Attempting auto-login...")
            self.load_session()
            
            # Refresh the page so the injected session data takes effect
            self.driver.refresh()
            time.sleep(5) 
            print("[Success] Logged in using saved session.")
        else:
            print("\n" + "="*50)
            print("[Action Required] No complete saved session found.")
            print("1. Please log in manually in the opened browser window.")
            print("2. Enter the SMS verification code.")
            print("3. Wait until you fully see your chats.")
            print("="*50 + "\n")
            
            input("Press ENTER in this console *ONLY AFTER* you have successfully logged in...")
            self.save_session()
            print("[Success] Session saved for future use.")
            
        return self.driver

    def save_session(self):
        """Extracts both Cookies and Local Storage to save the full authenticated state."""
        # 1. Save Cookies
        cookies = self.driver.get_cookies()
        with open(self.cookie_path, 'wb') as file:
            pickle.dump(cookies, file)
            
        # 2. Save Local Storage
        local_storage = self.driver.execute_script("return window.localStorage;")
        with open(self.local_storage_path, 'w') as file:
            json.dump(local_storage, file)
            
        print("[System] Cookies and Local Storage saved successfully.")

    def load_session(self):
        """Injects saved Cookies and Local Storage back into the browser."""
        # 1. Load Cookies
        with open(self.cookie_path, 'rb') as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                if 'rubika.ir' in cookie['domain']:
                    self.driver.add_cookie(cookie)
                    
        # 2. Load Local Storage
        with open(self.local_storage_path, 'r') as file:
            local_storage = json.load(file)
            for key, value in local_storage.items():
                # We pass key and value as arguments to prevent JS syntax errors if the data contains quotes
                self.driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)