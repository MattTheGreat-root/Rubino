from analyzer import Analyzer
from data_scraper import DataScraper
from rubika_auth import RubikaAuth
from broadcaster import Broadcaster

def main():
    while True:
        print("\n=== Rubino Smart Assistant ===")
        print("1. Scrape + Analyze")
        print("2. Load Offline Data")
        print("3. Send message to a Specific User")
        print("4. Send message to All Contacts")
        print("0. Exit")

        choice = input("\nSelect option: ")

        if choice == "1":
            auth = RubikaAuth()
            driver = auth.login()
            scraper = DataScraper(driver)
            
            target_shop = input("Target shop username (without @): ")
            
            if scraper.navigate_to_page(target_shop):
                data = scraper.scrape_all_posts(max_posts=20)
                scraper.save_to_csv(data)
                
                analyzer = Analyzer("data/scraped_products.csv")
                analyzer.run()

        elif choice == "2":
            analyzer = Analyzer("data/scraped_products.csv")
            analyzer.run()

        elif choice == "3":
            target_user = input("Enter target username to message (without @): ")
            message_text = input("Enter the message you want to send: ")
            
            auth = RubikaAuth()
            driver = auth.login()
            broadcaster = Broadcaster(driver)
            
            if broadcaster.navigate_to_messenger():
                broadcaster.send_to_list([target_user], test_message=message_text)

        elif choice == "4":
            print("[System] Warning: This will message all your Rubika contacts.")
            confirm = input("Are you sure you want to proceed? (y/n): ")
            
            if confirm.lower() == 'y':
                message_text = input("Enter the message you want to send to everyone: ")
                
                auth = RubikaAuth()
                driver = auth.login()
                broadcaster = Broadcaster(driver)
                
                if broadcaster.navigate_to_messenger():
                    broadcaster.broadcast_to_all(test_message=message_text)
            else:
                print("[System] Broadcast cancelled.")

        elif choice == "0":
            print("Exiting Rubino Smart Assistant. Saving session data...")
            try:
                driver.quit()
            except:
                pass
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()  