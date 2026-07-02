import time
from rubika_auth import RubikaAuth
from data_scraper import DataScraper

def main():
    print("--- Starting Rubino Smart Assistant ---")
    
    # Phase 1: Establish Session
    auth = RubikaAuth()
    driver = auth.login()
    
    # Phase 2: Scrape Page
    scraper = DataScraper(driver)
    
    # Prompt user for target page name
    target_shop = input("\nEnter target shop username (without @): ")
    
    scraper.navigate_to_page(target_shop)
    scraper.scroll_and_load_posts(scroll_cycles=3, pause_time=2)
    
    raw_data = scraper.extract_post_data()
    scraper.save_to_csv(raw_data)
    
    print("\n[System] Phase 2 Execution complete. CSV dataset populated.")

if __name__ == "__main__":
    main()