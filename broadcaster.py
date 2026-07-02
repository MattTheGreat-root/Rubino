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
        Mode 1: Iterates through a provided list of usernames, searches for them, 
        and dispatches the test message.
        """
        print(f"[Broadcaster] Starting Selected List mode for {len(username_list)} users.")
        
        for username in username_list:
            print(f" -> Processing user: {username}")
            try:
                # 1. Locate the Messenger search bar
                search_xpath = "//input[contains(@class, 'input-search-input') or @placeholder='جستجو']"
                search_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, search_xpath)))
                
                # 2. Clear and type the username
                self.driver.execute_script("arguments[0].click();", search_input)
                time.sleep(0.5)
                search_input.clear()
                self.driver.execute_script("arguments[0].value = '';", search_input)
                
                search_input.send_keys(username)
                print(f"    [Broadcaster] Searched for {username}. Waiting for results...")
                time.sleep(3) 
                
                # 3. Click the exact target profile from the search results
                exact_result_xpath = f"//span[text()='{username}'] | //div[contains(text(), '{username}')]"
                target_profile = self.wait.until(EC.element_to_be_clickable((By.XPATH, exact_result_xpath)))
                self.driver.execute_script("arguments[0].click();", target_profile)
                print(f"    [Success] Opened chat with {username}.")
                time.sleep(2) 
                
                # 4. TYPE AND SEND THE MESSAGE
                # Target the contenteditable rich text area
                chat_box_xpath = "//div[contains(@class, 'composer_rich_textarea') and @contenteditable='true']"
                chat_box = self.wait.until(EC.element_to_be_clickable((By.XPATH, chat_box_xpath)))
                
                # Click to focus
                self.driver.execute_script("arguments[0].click();", chat_box)
                time.sleep(0.5)
                
                # Clear existing drafts using JavaScript (Standard .clear() fails on divs)
                self.driver.execute_script("arguments[0].innerHTML = '';", chat_box)
                
                # Type the message
                chat_box.send_keys(test_message)
                time.sleep(1) # Brief pause to allow the UI to register the text and swap the send button
                
                # Send the message by simulating the ENTER key
                chat_box.send_keys(Keys.ENTER)
                print(f"    [Success] Message dispatched to {username}.")
                time.sleep(2) 
                
            except Exception as e:
                print(f"    [Error] Failed to process {username}: {str(e)}")
                
            finally:
                # Always return to the main messenger view before the next loop iteration
                self.navigate_to_messenger()
            
    def broadcast_to_all(self, test_message="This is a test message."):
        """
        Mode 2: Opens the new chat menu, scrapes all contact names into memory, 
        then uses the search logic to message them individually.
        """
        print("[Broadcaster] Starting Broadcast to All Contacts mode.")
        
        try:
            # 1. Click the floating "New Chat" button (Pencil icon)
            # We look for the common Rubika pencil icon class 'rbico-edit' or a primary circle button
            new_chat_xpath = "//button[.//i[contains(@class, 'rbico-edit')] or contains(@class, 'btn-circle')]"
            new_chat_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, new_chat_xpath)))
            self.driver.execute_script("arguments[0].click();", new_chat_btn)
            time.sleep(1)
            
            # 2. Click "New Message" or "New Chat" from the sub-menu if it appears
            # Bypassing the ripple effect to click the actual menu item
            new_message_menu_xpath = "//li[.//div[contains(@class, 'c-ripple')]]" 
            menu_items = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, new_message_menu_xpath)))
            if menu_items:
                self.driver.execute_script("arguments[0].click();", menu_items[0])
            time.sleep(2)
            
            # 3. Check if the contact list is empty (Based on your provided HTML)
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
                # Extract all currently rendered contact names
                # In Rubika, the name is usually inside an h3, span, or a div with class 'peer-title'
                contact_elements = self.driver.find_elements(By.XPATH, "//ul[contains(@class, 'contacts-container')]//li//div[contains(@class, 'peer-title')] | //ul[contains(@class, 'contacts-container')]//li//h3")
                
                for el in contact_elements:
                    name = el.text.strip()
                    if name and name not in extracted_names:
                        extracted_names.append(name)
                        print(f"    [Scraped] Found contact: {name}")

                # Scroll down slightly to load more contacts (Virtual Grid safe)
                self.driver.execute_script("arguments[0].scrollBy({top: 400, behavior: 'smooth'});", scroll_container)
                time.sleep(1.5)
                
                new_height = self.driver.execute_script("return arguments[0].scrollHeight;", scroll_container)
                
                # If scrolling didn't change the height, try forcing to the absolute bottom
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
            
            # 7. Feed the scraped names directly into your Mode 1 sender!
            if extracted_names:
                print("[Broadcaster] Transitioning to sending phase...")
                self.send_to_list(extracted_names, test_message)
                
        except Exception as e:
            print(f"[Error] Broadcast gathering failed: {str(e)}")
            self.navigate_to_messenger()