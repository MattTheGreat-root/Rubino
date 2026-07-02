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
        Navigates to the target shop profile strictly via UI clicks and searches,
        avoiding direct URL jumps to prevent point deductions.
        """
        print(f"[Scraper] Searching for target page: @{target_username}")
        wait = WebDriverWait(self.driver, 15)
        
        try:
            # 1. Locate and click the Search/Explore icon on Rubika Web UI
            # Note: Selectors may need adjustment based on Rubika's active DOM attributes
            search_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'search')] | //i[contains(@class, 'search')] | //div[@id='search-icon']")))
            search_tab.click()
            time.sleep(2)
            
            # 2. Locate the input bar, type the target username, and press Enter
            search_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='search'] | //input[@placeholder='Search']")))
            search_input.clear()
            search_input.send_keys(target_username)
            search_input.send_keys(Keys.ENTER)
            time.sleep(3)
            
            # 3. Locate the correct result from the search list and click it
            target_profile_item = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{target_username}')] | //span[contains(text(), '{target_username}')]")))
            target_profile_item.click()
            time.sleep(4)
            print(f"[Success] Arrived at @{target_username} profile via UI interaction.")
            
        except Exception as e:
            print(f"[Error] UI navigation failed: {str(e)}")
            print("[Fallback Hint] Ensure target element XPATH matches Rubika's current markup layout.")

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

    def extract_post_data(self):
        """
        Extracts HTML from Selenium, parses it with BeautifulSoup, 
        and extracts details using Regular Expressions.
        """
        print("[Scraper] Extracting DOM data using BeautifulSoup & Regex...")
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        products = []
        
        # Locate post wrappers (adjust container class names to match current m.rubika.ir markup)
        posts = soup.find_all('div', class_='rubino-post-container') # Placeholder class
        if not posts:
            # Secondary check if posts are structured inside standard grid cards
            posts = soup.find_all('div', class_='post-card') or soup.find_all('article')
            
        print(f"[Scraper] Found {len(posts)} structural post blocks.")
        
        for idx, post in enumerate(posts):
            try:
                # 1. Text Parsing for Price
                text_content = post.get_text(separator=" ")
                
                # Regex pattern matching common Persian numerical pricing formats (e.g., '120,000 تومان' or '۴۵۰,۰۰۰')
                # Catches both Western Arabic numbers and Eastern Arabic/Persian numbers
                price_match = re.search(r'([\d,]+|[\u06f0-\u06f9,]+)\s*(تومان|تومانی)?', text_content)
                price = price_match.group(1).replace(',', '') if price_match else "None"
                
                # Convert Persian numerals to standard digits if matched
                if price != "None":
                    price = self._convert_persian_nums(price)
                
                # 2. Extract Likes & Comments
                # Target the specific sub-elements containing these metric tallies
                likes_elem = post.find('span', class_='likes-count') or post.find(text=re.compile(r'لایک'))
                comments_elem = post.find('span', class_='comments-count') or post.find(text=re.compile(r'کامنت'))
                
                likes = re.sub(r'\D', '', self._convert_persian_nums(likes_elem.get_text())) if likes_elem else "0"
                comments = re.sub(r'\D', '', self._convert_persian_nums(comments_elem.get_text())) if comments_elem else "0"
                
                # Fallback check: if Regex couldn't find a price, we keep the row but flag it for Pandas to clean
                products.append({
                    'post_index': idx + 1,
                    'price': price if price else "None",
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