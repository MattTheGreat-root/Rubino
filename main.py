from data_scraper import DataScraper
from rubika_auth import RubikaAuth


def main():
    print("--- Starting Rubino Smart Assistant ---")

    # Phase 1: Establish Session
    auth = RubikaAuth()
    driver = auth.login()

    # Phase 2: Scrape Page
    scraper = DataScraper(driver)

    # Prompt user for target page name
    target_shop = input("\nEnter target shop username (without @): ")

    # Execute the navigation sequence
    if scraper.navigate_to_page(target_shop):
        
        # REMOVED the manual scroll_and_load_posts call here!
        # Claude's scrape_all_posts() method handles all scrolling automatically 
        # in micro-increments ONLY when it runs out of visible tiles.

        # Scrapes posts incrementally (handles infinite scroll / virtualization),
        # opening each new post, extracting its data, and returning to the grid.
        raw_data = scraper.scrape_all_posts(max_posts=20) # Added a safe limit for testing

        scraper.save_to_csv(raw_data)
        print(
            f"\n[System] Phase 2 Execution complete. {len(raw_data)} posts scraped into CSV dataset."
        )

    else:
        print("\n[System] Execution aborted due to navigation failure.")


if __name__ == "__main__":
    main()