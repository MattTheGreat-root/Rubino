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
        """
        Mode 1: Uses the proven DataScraper navigation to find the user's profile,
        clicks the direct 'Message' button on their page using a hardware-level simulation, 
        and sends the text natively.
        """
        print(f"[Broadcaster] Starting Selected List mode (Profile Bypass) for {len(username_list)} users.")
        
        # Import inside the method to avoid circular imports
        from data_scraper import DataScraper
        scraper = DataScraper(self.driver)
        
        for username in username_list:
            print(f" -> Processing user: {username}")
            try:
                # 1. Use the reliable Vitrin search
                print("    [Debug] Searching for user via Vitrin...")
                if not scraper.navigate_to_page(username):
                    print(f"    [Error] Could not find {username}. They may not have a Rubino profile.")
                    continue
                
                time.sleep(2) 
                
                # 2. Click the 'پیام' (Message) button on their profile
                print("    [Debug] Profile loaded. Performing hardware-level click...")
                
                # Target the SPAN directly, not the button wrapper. 
                msg_span_xpath = "//button/span[text()='پیام']"
                msg_span = self.wait.until(EC.presence_of_element_located((By.XPATH, msg_span_xpath)))
                
                # Force the element into the exact center of the viewport
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", msg_span)
                time.sleep(1)
                
                # Fake a literal human mouse sequence: move, down, wait, up
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(msg_span).click_and_hold().pause(0.2).release().perform()
                
                print(f"    [Success] Triggered SPA routing. Waiting for chat UI...")
                time.sleep(5) # Give the state machine plenty of time to transition
                
               # 3. TYPE AND SEND THE MESSAGE
                print("    [Debug] Locating chat input box...")
                
                # Target the exact Angular rich textarea from your HTML
                chat_box_xpath = "//div[contains(@class, 'composer_rich_textarea') and @contenteditable='true']"
                chat_box = self.wait.until(EC.presence_of_element_located((By.XPATH, chat_box_xpath)))
                
                # 1. Force the browser to focus the element via JavaScript
                self.driver.execute_script("arguments[0].focus();", chat_box)
                time.sleep(0.5)
                
                # 2. Use ActionChains to mimic a literal human typing on the keyboard
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                
                # 3. Execute a continuous hardware-level sequence: Move -> Click -> Type -> Enter
                actions.move_to_element(chat_box).click().pause(0.5)
                actions.send_keys(test_message).pause(1)
                actions.send_keys(Keys.ENTER).perform()
                
                print(f"    [Success] Message dispatched to {username}.")
                time.sleep(2)
            except Exception as e:
                print(f"    [Error] Failed to process {username}: {str(e)}")
            
            finally:
                # scraper.navigate_to_page() automatically resets to the Vitrin tab 
                # at the start of the next loop, so we don't need a back button!
                pass                        
                
    def broadcast_to_all(self, test_message="This is a test message."):
        """
        Mode 2: Opens the new chat menu, scrapes all contact names into memory, 
        then uses the search logic to message them individually.
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
            menu_items = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, new_message_menu_xpath)))
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
            
            # 6. Escape back to the main messenger to prepare for sending
            self.navigate_to_messenger()
            
            # 7. Feed the scraped names directly into your Mode 1 sender
            if extracted_names:
                print("[Broadcaster] Transitioning to sending phase...")
                self.send_to_list(extracted_names, test_message)
                
        except Exception as e:
            print(f"[Error] Broadcast gathering failed: {str(e)}")
            self.navigate_to_messenger()