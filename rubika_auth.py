import pickle
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class RubikaAuth:
    def __init__(self, cookie_dir='data', cookie_filename='cookies.pkl'):
        self.cookie_dir = cookie_dir
        self.cookie_path = os.path.join(self.cookie_dir, cookie_filename)
        self.base_url = "https://m.rubika.ir/"
        
        # Ensure the data directory exists for saving the cookies
        if not os.path.exists(self.cookie_dir):
            os.makedirs(self.cookie_dir)
            
        self.driver = self._initialize_driver()

    def _initialize_driver(self):
        """Sets up and returns the Selenium Chrome WebDriver."""
        print("[System] Initializing Chrome WebDriver...")
        chrome_options = Options()
        # Keeps the browser open after the script finishes (useful for debugging)
        chrome_options.add_experimental_option("detach", True) 
        
        # You can add arguments here later, like running headless, 
        # but for now we need the UI visible to log in.
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
        return driver

    def login(self):
        """Handles the logic of logging into Rubika."""
        print(f"[System] Navigating to {self.base_url}")
        self.driver.get(self.base_url)

        if os.path.exists(self.cookie_path):
            print("[System] Found saved cookies. Attempting auto-login...")
            self.load_cookies()
            # Refresh the page so the loaded cookies take effect
            self.driver.refresh()
            time.sleep(5) # Wait for the dynamic DOM to load the authenticated state
            print("[Success] Logged in using saved session.")
        else:
            print("\n" + "="*50)
            print("[Action Required] No saved session found.")
            print("1. Please log in manually in the opened browser window.")
            print("2. Enter the SMS verification code.")
            print("3. Wait until you fully see your chats.")
            print("="*50 + "\n")
            
            # Giving ample time to log in manually for the first time
            input("Press ENTER in this console *ONLY AFTER* you have successfully logged in...")
            self.save_cookies()
            print("[Success] Session saved for future use.")
            
        return self.driver

    def save_cookies(self):
        """Extracts cookies from the browser and saves them locally."""
        cookies = self.driver.get_cookies()
        with open(self.cookie_path, 'wb') as file:
            pickle.dump(cookies, file)
        print(f"[System] Cookies saved to {self.cookie_path}")

    def load_cookies(self):
        """Reads local cookies and injects them into the browser."""
        with open(self.cookie_path, 'rb') as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                # Selenium requires the domain to match exactly when adding cookies
                if 'rubika.ir' in cookie['domain']:
                    self.driver.add_cookie(cookie)