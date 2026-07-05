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
        """
        //*[@id="emoji-dropdown"]/div[1]/div[1]/div[1]/div[3]/div[1]/div/div[2]
        Safely escapes the Rubino feed and opens the main Messenger tab.
        """
        print("[Broadcaster] Navigating to main Messenger feed...")
        try:
            self.driver.switch_to.default_content()
            time.sleep(1)
            
            # Target the Messenger tab in the bottom nav
            messenger_tab_xpath = "//button[.//span[text()='پیام رسان']]"
            messenger_tab = self.wait.until(EC.element_to_be_clickable((By.XPATH, messenger_tab_xpath)))
            self.driver.execute_script("arguments[0].click();", messenger_tab)
            
            time.sleep(2)
            print("[Success] Reached Messenger home.")
            return True
            
        except Exception as e:
            print(f"[Warning] Failed to click Messenger tab. Forcing URL reload: {str(e)}")
            self.driver.get("https://m.rubika.ir/")
            time.sleep(4)
            return True

    def send_to_list(self, username_list, test_message="This is a test message."):
        print(f"[Broadcaster] Starting Selected List mode (Profile Bypass) for {len(username_list)} users.")
        
        from data_scraper import DataScraper
        scraper = DataScraper(self.driver)
        
        for username in username_list:
            print(f" -> Processing user: {username}")
            try:
                # 1. Search via Vitrin
                print("    [Debug] Searching for user via Vitrin...")
                if not scraper.navigate_to_page(username):
                    print(f"    [Error] Could not find {username}.")
                    continue
                
                time.sleep(2) 
                
                # 2. Click the 'پیام' (Message) button
                print("    [Debug] Profile loaded. Clicking 'Message' button...")
                msg_btn_xpath = "//button[.//span[text()='پیام']]"
                msg_btn = self.wait.until(EC.presence_of_element_located((By.XPATH, msg_btn_xpath)))
                self.driver.execute_script("arguments[0].click();", msg_btn)
                print(f"    [Success] Triggered SPA routing. Waiting for chat UI sandbox...")
                time.sleep(5) 
                
                # ==========================================
                # THE IFRAME BYPASS
                # ==========================================
                print("    [Debug] Breaching the <iframe> sandbox...")
                
                # Based on the HTML, the active chat iframe's URL contains 'openchat'
                iframe_xpath = "//iframe[contains(@src, 'openchat')]"
                
                # Tell Selenium to wait for the iframe to load, then step INSIDE it
                self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, iframe_xpath)))
                print("    [Debug] Successfully entered the chat iframe.")
                time.sleep(1)

                # 3. TYPE AND SEND THE MESSAGE
                print("    [Debug] Locating chat input box...")
                
                # Now that we are inside the iframe, Selenium can actually see the text box!
                chat_box_xpath = "//div[contains(@class, 'composer_rich_textarea') and @contenteditable='true']"
                chat_box = self.wait.until(EC.presence_of_element_located((By.XPATH, chat_box_xpath)))
                
                self.driver.execute_script("arguments[0].focus(); arguments[0].click();", chat_box)
                time.sleep(1)
                
                # The Angular bypass payload
                js_script = """
                    var box = arguments[0];
                    box.innerText = arguments[1];
                    box.dispatchEvent(new Event('input', { bubbles: true }));
                """
                self.driver.execute_script(js_script, chat_box, test_message)
                print("    [Debug] Text injected and Angular state updated.")
                time.sleep(1)
                
                chat_box.send_keys(Keys.ENTER)
                print(f"    [Success] Message dispatched to {username}.")
                time.sleep(2) 
                
            except Exception as e:
                print(f"    [Error] Failed to process {username}: {str(e)}")
            
            finally:
                # ==========================================
                # THE CLEANUP (CRITICAL)
                # ==========================================
                # Step back out of the iframe so the Vitrin search works for the next loop!
                self.driver.switch_to.default_content()

    def broadcast_to_all(self, test_message="This is a test message."):
        """
        Mode 2: Opens the new chat menu, scrapes all contact names into memory, 
        then uses the native Messenger search to bypass Vitrin and message them individually.
        """
        print("[Broadcaster] Starting Broadcast to All Contacts mode.")
        
        try:
            # 1. Click the floating "New Chat" button (Pencil icon)
            new_chat_xpath = "//button[.//i[contains(@class, 'rbico-edit')] or contains(@class, 'btn-circle')]"
            new_chat_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, new_chat_xpath)))
            self.driver.execute_script("arguments[0].click();", new_chat_btn)
            time.sleep(1)
            
            # 2. Click "New Message" or "New Chat" from the sub-menu if it appears
            new_message_menu_xpath = "//li[.//div[contains(@class, 'c-ripple')]]" 
            menu_items = self.driver.find_elements(By.XPATH, new_message_menu_xpath)
            if menu_items:
                self.driver.execute_script("arguments[0].click();", menu_items[0])
            time.sleep(2)
            
            # 3. Check if the contact list is empty
            empty_state = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'chatlist-empty')]")
            if empty_state:
                print("[Warning] No contacts found in this account ('هنوز مخاطبی در روبیکا ندارید').")
                print("[Broadcaster] Aborting broadcast. Please add contacts to test this feature.")
                self.navigate_to_messenger()
                return

            # 4. Locate the scrollable container and the list of contacts
            scroll_container_xpath = "//div[contains(@class, 'scrollable-y') and .//ul[contains(@class, 'contacts-container')]]"
            scroll_container = self.wait.until(EC.presence_of_element_located((By.XPATH, scroll_container_xpath)))
            
            print("[Broadcaster] Contact list opened. Initiating gathering sequence...")
            
            # 5. Scroll and Extract logic
            extracted_names = []
            last_height = self.driver.execute_script("return arguments[0].scrollHeight;", scroll_container)
            
            while True:
                contact_elements = self.driver.find_elements(By.XPATH, "//ul[contains(@class, 'contacts-container')]//li//div[contains(@class, 'peer-title')] | //ul[contains(@class, 'contacts-container')]//li//h3")
                
                for el in contact_elements:
                    name = el.text.strip()
                    if name and name not in extracted_names:
                        extracted_names.append(name)
                        print(f"    [Scraped] Found contact: {name}")

                self.driver.execute_script("arguments[0].scrollBy({top: 400, behavior: 'smooth'});", scroll_container)
                time.sleep(1.5)
                
                new_height = self.driver.execute_script("return arguments[0].scrollHeight;", scroll_container)
                
                if new_height == last_height:
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_container)
                    time.sleep(1.5)
                    final_height = self.driver.execute_script("return arguments[0].scrollHeight;", scroll_container)
                    
                    if final_height == last_height:
                        print("[Broadcaster] Reached the bottom of the contact list.")
                        break
                    else:
                        new_height = final_height
                        
                last_height = new_height

            print(f"[Success] Gathered a total of {len(extracted_names)} contacts.")
            
            # 6. Escape back to the main messenger to reset state
            self.navigate_to_messenger()
            
            if not extracted_names:
                return
            
            # 7. THE NATIVE MESSENGER SENDING LOOP
            print("[Broadcaster] Transitioning to sending phase...")
            
            for name in extracted_names:
                print(f" -> Processing contact: {name}")
                try:
                    # Open the new chat modal again
                    new_chat_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, new_chat_xpath)))
                    self.driver.execute_script("arguments[0].click();", new_chat_btn)
                    time.sleep(1)
                    
                    menu_items = self.driver.find_elements(By.XPATH, new_message_menu_xpath)
                    if menu_items:
                        self.driver.execute_script("arguments[0].click();", menu_items[0])
                    time.sleep(1.5)
                    
                    # Target the search bar inside the contacts modal
                    search_input_xpath = "//input[@type='text']" 
                    search_inputs = self.driver.find_elements(By.XPATH, search_input_xpath)
                    
                    active_search = None
                    for inp in search_inputs:
                        if inp.is_displayed():
                            active_search = inp
                            break
                            
                    if active_search:
                        active_search.clear()
                        active_search.send_keys(name)
                        time.sleep(1.5) # Wait for list to filter
                        
                    # Find and click the specific contact in the filtered list
                    safe_name = name.replace("'", "") # Prevent XPath crashes if name has an apostrophe
                    contact_xpath = f"//ul[contains(@class, 'contacts-container')]//li[.//div[contains(text(), '{safe_name}')] or .//h3[contains(text(), '{safe_name}')]]"
                    contact_els = self.driver.find_elements(By.XPATH, contact_xpath)
                    
                    if not contact_els:
                        print(f"    [Warning] Could not find {name} after searching. Skipping.")
                        self.navigate_to_messenger()
                        continue
                        
                    # Click the contact to open their chat
                    self.driver.execute_script("arguments[0].click();", contact_els[0])
                    print(f"    [Success] Opened chat for {name}. Waiting for iframe...")
                    time.sleep(3)
                    
                    # ==========================================
                    # THE IFRAME BYPASS (Copied from Mode 1)
                    # ==========================================
                    iframe_xpath = "//iframe[contains(@src, 'openchat')]"
                    self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, iframe_xpath)))
                    print("    [Debug] Successfully entered the chat iframe.")
                    time.sleep(1)

                    chat_box_xpath = "//div[contains(@class, 'composer_rich_textarea') and @contenteditable='true']"
                    chat_box = self.wait.until(EC.presence_of_element_located((By.XPATH, chat_box_xpath)))
                    
                    self.driver.execute_script("arguments[0].focus(); arguments[0].click();", chat_box)
                    time.sleep(1)
                    
                    js_script = """
                        var box = arguments[0];
                        box.innerText = arguments[1];
                        box.dispatchEvent(new Event('input', { bubbles: true }));
                    """
                    self.driver.execute_script(js_script, chat_box, test_message)
                    time.sleep(1)
                    
                    chat_box.send_keys(Keys.ENTER)
                    print(f"    [Success] Message dispatched to {name}.")
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"    [Error] Failed to process {name}: {str(e)}")
                    
                finally:
                    # CRITICAL: Always step back out of the iframe and reset to messenger for the next loop
                    self.driver.switch_to.default_content()
                    self.navigate_to_messenger()
                    
        except Exception as e:
            print(f"[Error] Broadcast gathering failed: {str(e)}")
            self.driver.switch_to.default_content()
            self.navigate_to_messenger()