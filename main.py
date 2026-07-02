import time
from rubika_auth import RubikaAuth
from data_scraper import DataScraper

def main():
    print("--- Starting Rubino Smart Assistant ---")
    
    # Phase 1: Establish Session
    auth = RubikaAuth()
    driver = auth.login()
    
# ... (Phase 1 Auth code remains the same) ...

    # Phase 2: Scrape Page
    scraper = DataScraper(driver)
    
    # Prompt user for target page name
    target_shop = input("\nEnter target shop username (without @): ")
    
    # Execute the navigation sequence
    if scraper.navigate_to_page(target_shop):
        
        # NEW: Open the first post to reveal the text/metrics
        if scraper.open_first_post():
            
            # Now we scroll the detailed feed, not the thumbnail grid
            scraper.scroll_and_load_posts(scroll_cycles=3, pause_time=2)
            
            # Extract and save the data
            raw_data = scraper.extract_post_data()
            scraper.save_to_csv(raw_data)
            print("\n[System] Phase 2 Execution complete. CSV dataset populated.")
            
        else:
            print("\n[System] Execution aborted due to grid interaction failure.")
    else:
        print("\n[System] Execution aborted due to navigation failure.")

if __name__ == "__main__":
    main()