# Rubino Smart Assistant

## Overview
The Rubino Smart Assistant is a Python-based automation, scraping, and data analysis tool designed for the Rubika/Rubino Web application. It leverages Selenium for complex Single Page Application (SPA) navigation, BeautifulSoup for DOM parsing, and Scikit-Learn for linear regression analysis. 

This project is specifically engineered to handle dynamic virtualized scrolling, bypass Angular state management, and inject payloads into iframe sandboxes for seamless automation.

## Project Structure
* `main.py`: The entry point of the application containing the interactive CLI menu.
* `rubika_auth.py`: Handles WebDriver initialization and persistent Chrome profile session management.
* `data_scraper.py`: Manages UI navigation, infinite scrolling, DOM rendering waits, and regex-based data extraction.
* `broadcaster.py`: Handles automated messaging, including contacts scraping and iframe/Angular context bypassing.
* `analyzer.py`: Loads extracted datasets to perform linear regression (Price vs. Engagement) and generates Matplotlib scatter plots.
* `requirements.txt`: Project dependencies.

## Prerequisites
* Python 3.8 or higher.
* Google Chrome browser.
* **Driver configuration (For restricted networks/Windows users):** Ensure the correct version of `chromedriver.exe` is placed directly in the root directory of this project. The system is designed to detect this local binary to bypass Selenium Manager's network download requirements.

## Installation
1. Clone or extract the project repository.
2. Open a terminal in the project root directory.
3. Install the required dependencies:
```bash
pip install -r requirements.txt
‍‍‍```

## Usage

Start the application by running the main script:

```bash
python main.py
```

## Initial Setup

On the first execution:

1. A Chrome window will open to the Rubika login page.
2. Log in manually using your credentials and SMS verification.
3. Wait for the main chat interface to fully load.
4. Return to the terminal and press **ENTER**.

> **Note:** The script uses a native Chrome profile. This login process is required only once.

## CLI Menu Options

### 1. Scrape + Analyze

- Prompts for a target shop username.
- Navigates to the Vitrin feed.
- Bypasses search overlays and scrapes pricing and engagement metrics.
- Saves the raw data to a CSV file.
- Immediately performs a linear regression analysis on the collected data.

### 2. Analyze Existing CSV

- Skips the scraping phase.
- Performs mathematical analysis and data visualization using the existing `data/scraped_products.csv` file.

### 3. Broadcaster (Specific User)

- Prompts for a target username and a custom message.
- Navigates directly to the user's chat.
- Bypasses the iframe sandbox.
- Updates the Angular application state using JavaScript.
- Dispatches the message.

### 4. Broadcaster (All Contacts)

- Iterates through the native Rubika contact list.
- Extracts all saved contact names into memory.
- Sequentially sends the specified message to every contact.

### 0. Exit

Safely terminates the WebDriver process and releases the Chrome profile lock.

Always use this option to close the application.

# Troubleshooting

## Chrome is already running (`SessionNotCreatedException`)

Chrome restricts profile directories to a single active process to prevent database corruption. If the script crashes or is terminated unexpectedly, a background Chrome process may continue holding the profile lock.

**Resolution**

Completely close all Chrome windows associated with the automation before restarting the script.

- **macOS:** `Cmd + Q`
- **Windows:** `Alt + F4`

## `ElementClickInterceptedException` During Navigation

Rubika's single-page application (SPA) may occasionally render overlapping UI elements during CSS transitions, preventing Selenium from interacting with the intended element.

**Resolution**

The `data_scraper.py` module includes JavaScript click fallbacks using:

```python
driver.execute_script("arguments[0].click();", element)
```

These bypass overlay interceptions by dispatching click events directly through the DOM.

If a severe UI freeze occurs, the script automatically resets to the base URL and retries the operation.