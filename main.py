from analyzer import Analyzer
from data_scraper import DataScraper
from rubika_auth import RubikaAuth


def main():
    print("=== Rubino Smart Assistant ===")
    print("1. Scrape + Analyze")
    print("2. Analyze Existing CSV")
    

    choice = input("Select option: ")

    if choice == "1":

        auth = RubikaAuth()
        driver = auth.login()

        scraper = DataScraper(driver)

        target_shop = input("Target shop: ")

        if scraper.navigate_to_page(target_shop):

            data = scraper.scrape_all_posts(max_posts=20)
            scraper.save_to_csv(data)

            analyzer = Analyzer("data/scraped_products.csv")
            analyzer.run()

    elif choice == "2":

        analyzer = Analyzer("data/scraped_products.csv")
        analyzer.run()

    # ... inside your choice logic in main.py ...

    elif choice == "3":
        auth = RubikaAuth()
        driver = auth.login()
        
        from broadcaster import Broadcaster
        broadcaster = Broadcaster(driver)
        
        # Test it by sending a message to yourself or a known test account!
        # Remember to navigate to the messenger first
        if broadcaster.navigate_to_messenger():
            test_list = ["farzannn1351"] # Replace with a safe test username
            broadcaster.send_to_list(test_list, "سلام! این یک پیام تست از طرف ربات است.")

    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()