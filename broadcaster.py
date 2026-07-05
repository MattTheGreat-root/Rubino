import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Broadcaster:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 15)

    def navigate_to_messenger(self):
        print("Mirim too Messenger...")
        try:
            self.driver.switch_to.default_content()
            time.sleep(1)
            
            peyam_resan_xpath = "//button[.//span[text()='پیام رسان']]"
            tab = self.wait.until(EC.element_to_be_clickable((By.XPATH, peyam_resan_xpath)))
            self.driver.execute_script("arguments[0].click();", tab)
            
            time.sleep(2)
            return True
            
        except Exception:
            self.driver.get("https://m.rubika.ir/")
            time.sleep(4)
            return True

    def send_to_list(self, username_list, test_message="Test"):
        print(f"Ersal be {len(username_list)} nafar (Profile Bypass).")
        
        from data_scraper import DataScraper
        scraper = DataScraper(self.driver)
        
        for karbar in username_list:
            print(f" -> Karbar: {karbar}")
            try:
                if not scraper.navigate_to_page(karbar):
                    print(f"Peyda nashod: {karbar}")
                    continue
                
                time.sleep(2) 
                
                dokme_payam = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[.//span[text()='پیام']]")))
                self.driver.execute_script("arguments[0].click();", dokme_payam)
                time.sleep(5) 
                
                # Iframe bypass
                iframe_xpath = "//iframe[contains(@src, 'openchat')]"
                self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, iframe_xpath)))
                time.sleep(1)

                payam_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'composer_rich_textarea') and @contenteditable='true']")))
                self.driver.execute_script("arguments[0].focus(); arguments[0].click();", payam_box)
                time.sleep(2)
                
                # Angular JS bypass
                js_script = """
                    var box = arguments[0];
                    box.innerText = arguments[1];
                    box.dispatchEvent(new Event('input', { bubbles: true }));
                """
                self.driver.execute_script(js_script, payam_box, test_message)
                time.sleep(2)
                
                payam_box.send_keys(Keys.ENTER)
                print(f"Payam ersal shod be {karbar}.")
                time.sleep(3) 
                
            except Exception as e:
                print(f"Khata baraye {karbar}: {str(e)}")
            finally:
                self.driver.switch_to.default_content()

    def broadcast_to_all(self, test_message="Test"):
        print("Ersal be hameye mokhatebin...")
        
        try:
            chat_jadid = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//i[contains(@class, 'rbico-edit')] or contains(@class, 'btn-circle')]")))
            self.driver.execute_script("arguments[0].click();", chat_jadid)
            time.sleep(1)
            
            menu_items = self.driver.find_elements(By.XPATH, "//li[.//div[contains(@class, 'c-ripple')]]")
            if menu_items:
                self.driver.execute_script("arguments[0].click();", menu_items[0])
            time.sleep(2)
            
            if self.driver.find_elements(By.XPATH, "//li[contains(@class, 'chatlist-empty')]"):
                print("Mokhatebi nist!")
                self.navigate_to_messenger()
                return

            scroll_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'scrollable-y') and .//ul[contains(@class, 'contacts-container')]]")))
            
            mokhatebin = []
            last_h = self.driver.execute_script("return arguments[0].scrollHeight;", scroll_box)
            
            while True:
                elements = self.driver.find_elements(By.XPATH, "//ul[contains(@class, 'contacts-container')]//li//div[contains(@class, 'peer-title')] | //ul[contains(@class, 'contacts-container')]//li//h3")
                
                for el in elements:
                    esm = el.text.strip()
                    if esm and esm not in mokhatebin:
                        mokhatebin.append(esm)
                        print(f"Peyda shod: {esm}")

                self.driver.execute_script("arguments[0].scrollBy({top: 400, behavior: 'smooth'});", scroll_box)
                time.sleep(1.5)
                
                new_h = self.driver.execute_script("return arguments[0].scrollHeight;", scroll_box)
                
                if new_h == last_h:
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_box)
                    time.sleep(1.5)
                    final_h = self.driver.execute_script("return arguments[0].scrollHeight;", scroll_box)
                    
                    if final_h == last_h:
                        break
                    else:
                        new_h = final_h
                        
                last_h = new_h

            print(f"Kol: {len(mokhatebin)} nafar.")
            self.navigate_to_messenger()
            
            if not mokhatebin:
                return
            
            for esm in mokhatebin:
                print(f" -> Ersal be: {esm}")
                try:
                    chat_jadid = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//i[contains(@class, 'rbico-edit')] or contains(@class, 'btn-circle')]")))
                    self.driver.execute_script("arguments[0].click();", chat_jadid)
                    time.sleep(1)
                    
                    menu_items = self.driver.find_elements(By.XPATH, "//li[.//div[contains(@class, 'c-ripple')]]")
                    if menu_items:
                        self.driver.execute_script("arguments[0].click();", menu_items[0])
                    time.sleep(1.5)
                    
                    search_inputs = self.driver.find_elements(By.XPATH, "//input[@type='text']")
                    active_search = next((inp for inp in search_inputs if inp.is_displayed()), None)
                            
                    if active_search:
                        active_search.clear()
                        active_search.send_keys(esm)
                        time.sleep(1.5)
                        
                    safe_esm = esm.replace("'", "") 
                    contact_els = self.driver.find_elements(By.XPATH, f"//ul[contains(@class, 'contacts-container')]//li[.//div[contains(text(), '{safe_esm}')] or .//h3[contains(text(), '{safe_esm}')]]")
                    
                    if not contact_els:
                        self.navigate_to_messenger()
                        continue
                        
                    self.driver.execute_script("arguments[0].click();", contact_els[0])
                    time.sleep(3)
                    
                    # Iframe bypass
                    iframe_xpath = "//iframe[contains(@src, 'openchat')]"
                    self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, iframe_xpath)))
                    time.sleep(1)

                    payam_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'composer_rich_textarea') and @contenteditable='true']")))
                    self.driver.execute_script("arguments[0].focus(); arguments[0].click();", payam_box)
                    time.sleep(1)
                    
                    js_script = """
                        var box = arguments[0];
                        box.innerText = arguments[1];
                        box.dispatchEvent(new Event('input', { bubbles: true }));
                    """
                    self.driver.execute_script(js_script, payam_box, test_message)
                    time.sleep(2)
                    
                    payam_box.send_keys(Keys.ENTER)
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Khata ersal be {esm}: {str(e)}")
                    
                finally:
                    self.driver.switch_to.default_content()
                    self.navigate_to_messenger()
                    
        except Exception as e:
            print(f"Khata koli: {str(e)}")
            self.driver.switch_to.default_content()
            self.navigate_to_messenger()