import os
import re
import csv
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class DataScraper:
    def __init__(self, driver, output_dir='data', output_filename='scraped_products.csv'):
        self.driver = driver
        self.output_dir = output_dir
        self.output_path = os.path.join(self.output_dir, output_filename)
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def navigate_to_page(self, target_username):
        """
        Navigates to the target Rubino profile via the Vitrin (Explore) page.
        """
        print(f"[Scraper] Executing navigation sequence to Vitrin for: @{target_username}")
        wait = WebDriverWait(self.driver, 15)
        
        try:
            # 1. Ensure we are in the main document
            self.driver.switch_to.default_content()
            time.sleep(1) 
            
            # 2. Click the 'ویترین' (Vitrin) tab from the bottom navigation
            vitrin_tab_xpath = "//button[.//span[text()='ویترین']]"
            vitrin_tab = wait.until(EC.element_to_be_clickable((By.XPATH, vitrin_tab_xpath)))
            self.driver.execute_script("arguments[0].click();", vitrin_tab)
            print("[Scraper] Navigated to Vitrin section.")
            
            time.sleep(1) 
            
            # 3. Click the "Dummy" search bar trigger on the main Vitrin feed
            # Targeting the element containing the word "جستجو" at the top
            dummy_search_trigger_xpath = "//*[text()='جستجو' or contains(@placeholder, 'جستجو')]"
            dummy_search_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, dummy_search_trigger_xpath)))
            self.driver.execute_script("arguments[0].click();", dummy_search_trigger)
            print("[Scraper] Opened dedicated search view.")
            
            time.sleep(1) # Wait for the new search view to slide in
            
            # 4. Locate the ACTUAL text input field on the new search page
            # As seen in your screenshot, the placeholder here is 'جستجوی کاربر'
            actual_search_input_xpath = "//input[contains(@placeholder, 'جستجوی کاربر') or @type='text']"
            actual_search_input = wait.until(EC.element_to_be_clickable((By.XPATH, actual_search_input_xpath)))
            
            # Click, clear, and type the target username
            actual_search_input.click()
            time.sleep(1)
            actual_search_input.clear()
            actual_search_input.send_keys(target_username)
            actual_search_input.send_keys(Keys.ENTER)
            print(f"[Scraper] Searching for user: {target_username}")
            
            time.sleep(3) 
            
            # 5. Click the matching profile from the search results
            exact_result_xpath = f"//div[contains(text(), '{target_username}')] | //span[contains(text(), '{target_username}')]"
            target_profile_item = wait.until(EC.presence_of_element_located((By.XPATH, exact_result_xpath)))
            self.driver.execute_script("arguments[0].click();", target_profile_item)
            
            time.sleep(3) 
            print(f"[Success] Arrived at @{target_username} Rubino profile.")
            return True
            
        except Exception as e:
            print(f"[Error] Vitrin UI navigation failed: {str(e)}")
            print("[Fallback Hint] Check if the search returned zero results or if elements intercepted the click.")
            return False
                              
    def scroll_and_load_posts(self, scroll_cycles=5, pause_time=2):
        """
        Injects JavaScript to handle dynamic scrolling to force Rubika's 
        lazy loader into rendering historical posts.
        """
        print(f"[Scraper] Initializing automated scrolling ({scroll_cycles} cycles)...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for i in range(scroll_cycles):
            # Scroll down to the bottom of the page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause_time)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            print(f"[Log] Scroll cycle {i+1}/{scroll_cycles} complete. Loading dynamic DOM...")
            
            if new_height == last_height:
                print("[Scraper] Reached the end of the profile timeline.")
                break
            last_height = new_height

    def open_first_post(self):
        """
        Transitions from the profile grid view into the detailed scrollable feed view.
        Uses JavaScript to dynamically find the first large SQUARE image (grid thumbnail) 
        and bypasses banners/avatars.
        """
        print("[Scraper] Clicking the first post to open the detailed feed...")
        wait = WebDriverWait(self.driver, 15)
        
        try:
            # Wait until at least one external image is loaded
            wait.until(EC.presence_of_element_located((By.XPATH, "//img[starts-with(@src, 'http')]")))
            time.sleep(2) 
            
            # JavaScript to find the first image larger than 100px that is perfectly SQUARE
            js_script = """
            let imgs = document.querySelectorAll('img[src^="http"]');
            for (let i = 0; i < imgs.length; i++) {
                let rect = imgs[i].getBoundingClientRect();
                
                // Check if width > 100 AND width matches height (allowing a 2px margin for sub-pixel rendering)
                if (rect.width > 100 && Math.abs(rect.width - rect.height) <= 2) {
                    imgs[i].click();
                    return true;
                }
            }
            return false;
            """
            success = self.driver.execute_script(js_script)
            
            if success:
                time.sleep(4) 
                print("[Success] Detailed post feed opened.")
                return True
            else:
                print("[Error] No valid square grid thumbnails found on the screen.")
                return False
                
        except Exception as e:
            print(f"[Error] Failed to open the first post: {str(e)}")
            return False
                        
    def extract_post_data(self):
        """
        Extracts HTML from Selenium, parses it with BeautifulSoup, 
        and extracts details using unified Regex tailored to handle both 
        photo and video posts dynamically.
        """
        print("[Scraper] Extracting DOM data using BeautifulSoup & Regex...")
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        products = []
        
        # Locate all primary containers. Both the photo and video HTML snippets 
        # share this exact structural footprint.
        all_containers = soup.find_all('div', attrs={"width": "100%", "display": "flex"})
        
        valid_posts = []
        for container in all_containers:
            text = container.get_text()
            # A valid post must contain engagement metrics (Likes, Views, or Comments).
            # This filters out random UI elements like headers or navbars.
            if re.search(r'(لایک|مشاهده|کامنت)', text) and container not in valid_posts:
                valid_posts.append(container)
            
        print(f"[Scraper] Found {len(valid_posts)} structural post blocks.")
        
        for idx, post in enumerate(valid_posts):
            try:
                # Extract all text and separate with spaces for clean regex parsing
                text_content = post.get_text(separator=" ")
                
                # 1. Regex for Price (e.g., "1500 تومان" or "۴۵۰ هزار")
                price_match = re.search(r'([\d,]+|[\u06f0-\u06f9,]+)\s*(تومان|تومانی|هزار|ریال)', text_content)
                price = price_match.group(1).replace(',', '') if price_match else "None"
                
                if price != "None":
                    price = self._convert_persian_nums(price)
                
                # 2. Regex for Likes OR Views (Videos show 'مشاهده' instead of 'لایک')
                likes_match = re.search(r'([\d۰-۹,]+)\s*(لایک|مشاهده)', text_content)
                likes = likes_match.group(1).replace(',', '') if likes_match else "0"
                likes = self._convert_persian_nums(likes)
                
                # 3. Regex for Comments (Safely defaults to 0 if not found)
                comments_match = re.search(r'([\d۰-۹,]+)\s*کامنت', text_content)
                comments = comments_match.group(1).replace(',', '') if comments_match else "0"
                comments = self._convert_persian_nums(comments)
                
                # Append cleaned data to the dataset
                products.append({
                    'post_index': idx + 1,
                    'price': price if price != "None" else "None",
                    'likes': int(likes) if likes.isdigit() else 0,
                    'comments': int(comments) if comments.isdigit() else 0
                })
                
            except Exception as e:
                print(f"[Warning] Error parsing item index {idx}: {str(e)}")
                continue
                
        return products
    
    def save_to_csv(self, product_list):
        """Writes data into a structured CSV file for downstream ML analysis."""
        with open(self.output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['post_index', 'price', 'likes', 'comments']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for product in product_list:
                writer.writerow(product)
                
        print(f"[Success] Extracted raw dataset successfully exported to {self.output_path}")

    def _convert_persian_nums(self, text):
        """Helper utility converting Persian/Arabic digit characters to standard English integers."""
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        arabic_digits = '٠١٢٣٤٥٦٧٨٩'
        english_digits = '0123456789'
        
        translation_table = str.maketrans(persian_digits + arabic_digits, english_digits * 2)
        return text.translate(translation_table)