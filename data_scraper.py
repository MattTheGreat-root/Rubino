import csv
import os
import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class DataScraper:
    def __init__(
        self, driver, output_dir="data", output_filename="scraped_products.csv"
    ):
        self.driver = driver
        self.output_dir = output_dir
        self.output_path = os.path.join(self.output_dir, output_filename)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def navigate_to_page(self, target_username):
        """
        Navigates to the target Rubino profile via the Vitrin (Explore) page.
        """
        print(
            f"[Scraper] Executing navigation sequence to Vitrin for: @{target_username}"
        )
        wait = WebDriverWait(self.driver, 15)

        try:
            # 1. Ensure we are in the main document
            self.driver.switch_to.default_content()
            time.sleep(1)

            # 2. Click the 'ویترین' (Vitrin) tab from the bottom navigation
            vitrin_tab_xpath = "//button[.//span[text()='ویترین']]"
            vitrin_tab = wait.until(
                EC.element_to_be_clickable((By.XPATH, vitrin_tab_xpath))
            )
            self.driver.execute_script("arguments[0].click();", vitrin_tab)
            print("[Scraper] Navigated to Vitrin section.")

            time.sleep(1)

            # 3. Click the "Dummy" search bar trigger on the main Vitrin feed
            # Targeting the element containing the word "جستجو" at the top
            dummy_search_trigger_xpath = (
                "//*[text()='جستجو' or contains(@placeholder, 'جستجو')]"
            )
            dummy_search_trigger = wait.until(
                EC.element_to_be_clickable((By.XPATH, dummy_search_trigger_xpath))
            )
            self.driver.execute_script("arguments[0].click();", dummy_search_trigger)
            print("[Scraper] Opened dedicated search view.")

            time.sleep(1)  # Wait for the new search view to slide in

            # 4. Locate the ACTUAL text input field on the new search page
            # As seen in your screenshot, the placeholder here is 'جستجوی کاربر'
            actual_search_input_xpath = (
                "//input[contains(@placeholder, 'جستجوی کاربر') or @type='text']"
            )
            actual_search_input = wait.until(
                EC.element_to_be_clickable((By.XPATH, actual_search_input_xpath))
            )

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
            target_profile_item = wait.until(
                EC.presence_of_element_located((By.XPATH, exact_result_xpath))
            )
            self.driver.execute_script("arguments[0].click();", target_profile_item)

            time.sleep(3)
            print(f"[Success] Arrived at @{target_username} Rubino profile.")
            return True

        except Exception as e:
            print(f"[Error] Vitrin UI navigation failed: {str(e)}")
            print(
                "[Fallback Hint] Check if the search returned zero results or if elements intercepted the click."
            )
            return False

    def _find_scrollable_ancestor(self):
        """
        Rubika's post grid lives inside a nested div with its own
        'overflow: auto/scroll' (confirmed directly in the page source, e.g.
        class 'rtl-l3f8vc' with inline style 'overflow: auto'), NOT the
        document body. Scrolling window/body (the old approach) was a no-op,
        which is why only the initially-rendered batch of tiles was ever found.
        This walks up from a real post tile to find that actual scrollable
        container dynamically, so it keeps working even if class names change.
        """
        return self.driver.execute_script(
            """
            let img = document.querySelector('div[width][height] img[src*="/picture/"]');
            if (!img) return null;
            let el = img.parentElement;
            while (el && el !== document.body) {
                let style = window.getComputedStyle(el);
                if (style.overflowY === 'auto' || style.overflowY === 'scroll' ||
                    style.overflow === 'auto' || style.overflow === 'scroll') {
                    return el;
                }
                el = el.parentElement;
            }
            return null;
            """
        )

    def scroll_and_load_posts(self, scroll_cycles=5, pause_time=2.0):
        """
        Injects JavaScript to handle dynamic scrolling to force Rubika's
        lazy loader into rendering historical posts. Scrolls the actual
        internal scrollable grid container (see _find_scrollable_ancestor),
        falling back to window scrolling if that container can't be found.
        """
        print(f"[Scraper] Initializing automated scrolling ({scroll_cycles} cycles)...")
        container = self._find_scrollable_ancestor()

        if container is None:
            print(
                "[Warning] Could not locate the grid's scrollable container; "
                "falling back to window scrolling (may not load more posts)."
            )
            last_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )
            for i in range(scroll_cycles):
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(pause_time)
                new_height = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                print(
                    f"[Log] Scroll cycle {i + 1}/{scroll_cycles} complete. Loading dynamic DOM..."
                )
                if new_height == last_height:
                    print("[Scraper] Reached the end of the profile timeline.")
                    break
                last_height = new_height
            return

        last_height = self.driver.execute_script(
            "return arguments[0].scrollHeight;", container
        )
        for i in range(scroll_cycles):
            self.driver.execute_script(
                "arguments[0].scrollTo(0, arguments[0].scrollHeight);", container
            )
            time.sleep(pause_time)

            new_height = self.driver.execute_script(
                "return arguments[0].scrollHeight;", container
            )
            print(
                f"[Log] Scroll cycle {i + 1}/{scroll_cycles} complete. Loading dynamic DOM..."
            )

            if new_height == last_height:
                print("[Scraper] Reached the end of the profile timeline.")
                break
            last_height = new_height

    def _wait_for_post_images_loaded(self, timeout=15):
        """
        Waits until every currently-present post image has actually finished
        loading (naturalWidth > 0). Rubika's grid renders at least twice: an
        early pass before images/highlights are ready, and a final pass once
        everything is loaded. Measuring positions before the final pass gives
        stale coordinates, which was the root cause of clicks landing on the
        wrong element.
        """
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script(
                """
                let imgs = document.querySelectorAll('img[src*="/picture/"]');
                if (imgs.length === 0) return false;
                return Array.from(imgs).every(img => img.complete && img.naturalWidth > 0);
                """
            )
        )

    def find_post_tiles(self):
        """
        Returns the list of Selenium WebElements for post tiles currently rendered
        in the profile grid, one per visual grid cell. A tile is identified
        structurally: a <div> carrying its own numeric width/height HTML
        attributes that are equal (a square thumbnail cell), containing a real
        post <img> whose src includes '/picture/' (as opposed to avatar/banner
        images or inline <svg> tab icons), and not living inside a nav/tab bar.

        Rubika's grid re-renders at least once after the initial paint (e.g. once
        the profile header/highlights finish loading), and the earlier render's
        DOM nodes are NOT cleaned up -- they remain in the document with stale
        bounding-box coordinates that no longer correspond to anything visible.
        Both the stale and the current nodes match the same structural fingerprint,
        so we deduplicate by rounded visual position (rect.left/rect.top),
        keeping only the LAST matching node per grid cell, since the current
        (correct) render consistently appears later in DOM order than the stale one.
        """
        self._wait_for_post_images_loaded()

        xpath = (
            "//div[@width and @height]"
            "[.//img[contains(@src, '/picture/')]]"
            "[not(ancestor::nav) and not(ancestor::header)]"
        )
        candidates = self.driver.find_elements(By.XPATH, xpath)

        size_filtered = []
        for tile in candidates:
            try:
                w = float(tile.get_attribute("width"))
                h = float(tile.get_attribute("height"))
                if w > 100 and abs(w - h) <= 2 and tile.is_displayed():
                    size_filtered.append(tile)
            except (TypeError, ValueError):
                continue

        if not size_filtered:
            return []

        # Deduplicate by visual position: for each (rounded) grid cell, keep the
        # LAST matching DOM node, sorted into natural RTL reading order
        # (top-to-bottom, right-to-left, since higher `left` = further right).
        dedup_info = self.driver.execute_script(
            """
            let els = arguments[0];
            return els.map(el => {
                let rect = el.getBoundingClientRect();
                return [Math.round(rect.top / 5) * 5, Math.round(rect.left / 5) * 5];
            });
            """,
            size_filtered,
        )

        by_position = {}
        for tile, (top, left) in zip(size_filtered, dedup_info):
            by_position[(top, left)] = tile  # later entries overwrite earlier ones

        ordered_positions = sorted(
            by_position.keys(), key=lambda pos: (pos[0], -pos[1])
        )
        deduped_tiles = [by_position[pos] for pos in ordered_positions]

        # Some structurally-matching nodes are clipped/hidden by an ancestor
        # (e.g. overflow:hidden), which Selenium's is_displayed() does not
        # detect -- they report a plausible bounding box but are not actually
        # what's visually on screen at that position (verified: one such node
        # turned out to be an unrelated video-preview component). We drop any
        # tile that isn't genuinely the topmost element at its own center.
        topmost_flags = self.driver.execute_script(
            """
            let els = arguments[0];
            return els.map(el => {
                let rect = el.getBoundingClientRect();
                let cx = rect.left + rect.width / 2;
                let cy = rect.top + rect.height / 2;
                let topEl = document.elementFromPoint(cx, cy);
                return !!topEl && (topEl === el || el.contains(topEl));
            });
            """,
            deduped_tiles,
        )

        return [
            tile for tile, is_topmost in zip(deduped_tiles, topmost_flags) if is_topmost
        ]

    def count_available_tiles(self):
        """Returns how many valid post tiles are currently rendered in the grid."""
        return len(self.find_post_tiles())

    def scrape_all_posts(self, max_posts=None):
        """
        Scrapes price/likes/comments across the whole profile grid, handling
        virtualized/infinite scroll correctly. find_post_tiles() only reflects
        tiles currently rendered in the viewport (older ones get unmounted as you
        scroll further), so pre-counting a fixed total and looping by index
        doesn't work here. Instead, each round we look for the first tile whose
        image src we haven't scraped yet; if none is found, we scroll for more.
        We stop once scrolling repeatedly turns up no new tiles (end of feed).
        """
        seen_srcs = set()
        results = []
        stagnant_rounds = 0
        max_stagnant_rounds = 3

        while True:
            if max_posts is not None and len(results) >= max_posts:
                break

            tiles = self.find_post_tiles()
            target_index = None
            target_src = None
            for i, tile in enumerate(tiles):
                try:
                    src = tile.find_element(By.TAG_NAME, "img").get_attribute("src")
                except Exception:
                    continue
                if src and src not in seen_srcs:
                    target_index = i
                    target_src = src
                    break

            if target_index is None:
                stagnant_rounds += 1
                print(
                    f"[Scraper] No new tiles visible "
                    f"({stagnant_rounds}/{max_stagnant_rounds}); scrolling for more..."
                )
                if stagnant_rounds >= max_stagnant_rounds:
                    print("[Scraper] No more new posts found; stopping.")
                    break
                self.scroll_and_load_posts(scroll_cycles=2, pause_time=1.5)
                continue

            stagnant_rounds = 0
            seen_srcs.add(target_src)

            if self.open_post_by_index(target_index):
                data = self.extract_single_post_data()
                if data:
                    data["post_index"] = len(results) + 1
                    results.append(data)
                    print(f"[Scraper] Scraped post {len(results)}: {data}")
                else:
                    print("[Warning] Post opened but no data could be extracted.")
                self.go_back_to_grid()
            else:
                print("[Warning] Failed to open a tile; skipping it and continuing.")

        return results

    def _click_tile_with_retry(self, index, attempts=3):
        """
        Re-fetches the tile list and clicks the tile at `index` using Selenium's
        NATIVE element click (not ActionChains, not JS execute_script). Rubika's
        grid re-renders periodically (likely due to live like/view counters),
        which can leave stale, covered, or repositioned tile references behind.
        Native .click() properly detects obstruction/staleness and raises a
        catchable exception instead of silently clicking the wrong element, so we
        retry with a freshly re-fetched tile list when that happens.
        """
        from selenium.common.exceptions import (
            ElementClickInterceptedException,
            StaleElementReferenceException,
        )

        for attempt in range(1, attempts + 1):
            tiles = self.find_post_tiles()
            if not tiles or index >= len(tiles):
                print(
                    f"[Warning] Attempt {attempt}/{attempts}: no post tile found at "
                    f"index {index} (found {len(tiles)} tiles); retrying..."
                )
                time.sleep(1)
                continue

            target_tile = tiles[index]
            try:
                target_tile.click()
                return True
            except (
                ElementClickInterceptedException,
                StaleElementReferenceException,
            ) as e:
                print(
                    f"[Warning] Click attempt {attempt}/{attempts} on tile {index} "
                    f"failed ({type(e).__name__}); retrying with a fresh tile list..."
                )
                print(f"[Debug] Exception detail: {str(e)[:500]}")
                time.sleep(0.5)

        print(
            f"[Error] Could not reliably click tile {index} after {attempts} attempts."
        )
        return False

    def open_post_by_index(self, index):
        """
        Opens a specific post tile (by its position in the currently rendered grid)
        via _click_tile_with_retry(), which uses Selenium's native element click
        against a freshly re-fetched, deduplicated tile list (see find_post_tiles()
        for why deduplication and freshness both matter here).
        """
        print(f"[Scraper] Opening post tile at index {index}...")
        wait = WebDriverWait(self.driver, 15)

        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//img[contains(@src, '/picture/')]")
                )
            )
            time.sleep(1)

            success = self._click_tile_with_retry(index, attempts=5)
            if not success:
                return False

            # Verify the post detail view ACTUALLY opened by waiting for its like
            # count text to appear (verified format: "<strong>0</strong> لایک",
            # always rendered even when the count is zero). If the click was a
            # no-op, we must not report success -- doing so would trigger a
            # go_back_to_grid() call with nothing to back out of, which was
            # overshooting into the explore feed.
            try:
                WebDriverWait(self.driver, 6).until(
                    lambda d: (
                        "لایک" in d.execute_script("return document.body.innerText;")
                    )
                )
            except Exception:
                print(
                    f"[Error] Post index {index} was clicked but no post detail view appeared."
                )
                return False

            time.sleep(1)
            print(f"[Success] Post index {index} opened.")
            return True

        except Exception as e:
            print(f"[Error] Failed to open post at index {index}: {str(e)}")
            return False

    def go_back_to_grid(self):
        """
        Navigates back from an opened post detail view to the profile grid using
        the app's own in-UI back button (an arrow icon), rather than driver.back().
        Browser history navigation was found to overshoot past the shop's grid
        entirely, landing on the main explore feed instead.

        The back button's wrapper div carries a distinctive class
        ('rtl-1x9eqjj', verified against the real page). We cannot XPath-match on
        the arrow's own <svg>/<path> (SVG elements live in a separate XML
        namespace, so 'contains(@d, ...)' style XPath queries silently match
        nothing in this browser even though the text is present in page_source).
        Rubika keeps multiple tab panels mounted simultaneously (search view,
        home, post detail, ...), each with their own header reusing this same
        class, so is_displayed() alone isn't enough to disambiguate -- inactive
        tabs are pushed off-screen via a CSS transform rather than hidden, so we
        additionally check that the candidate's bounding box actually falls
        inside the current viewport.
        """
        try:
            candidates = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'rtl-1x9eqjj')]"
            )
            in_viewport = self.driver.execute_script(
                """
                let els = arguments[0];
                return els.map(el => {
                    let rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0 &&
                        rect.left >= -1 && rect.left < window.innerWidth;
                });
                """,
                candidates,
            )
            visible_candidates = [el for el, ok in zip(candidates, in_viewport) if ok]

            if not visible_candidates:
                print("[Warning] No back button found; falling back to driver.back().")
                self.driver.back()
                time.sleep(2)
                return

            back_button = visible_candidates[0]
            try:
                # Native click raises ElementClickIntercepted here: ChromeDriver's
                # obstruction check treats the button's own child <path> (SVG,
                # different XML namespace) as "another element" on top, even
                # though it's clearly a descendant. This is a static, always-
                # present nav icon (not subject to the grid's live-render churn),
                # so a plain JS click is safe and sidesteps that false positive.
                self.driver.execute_script("arguments[0].click();", back_button)
                time.sleep(2)
            except Exception as e:
                print(
                    f"[Warning] JS click on back button failed ({str(e)}); "
                    f"falling back to driver.back()."
                )
                self.driver.back()
                time.sleep(2)

        except Exception as e:
            print(f"[Warning] Failed to locate in-app back button: {str(e)}")
            self.driver.back()
            time.sleep(2)

    def _parse_engagement_text(self, text_content):
        """
        Given the raw text of a post's info block, extracts price, likes/views,
        and comments using regex, and normalizes Persian/Arabic digits.
        """
        # 1. Regex for Price. Rubika captions write it as "قیمت 925" (the word
        # "price" followed by the number, no currency suffix) -- verified directly
        # against a real post's caption text. We try that pattern first, and fall
        # back to a "1500 تومان" / "۴۵۰ هزار" style suffix pattern in case some
        # sellers format captions differently.
        price_match = re.search(
            r"قیمت\s*[:：]?\s*([\d,]+|[\u06f0-\u06f9,]+)",
            text_content,
        )
        if not price_match:
            price_match = re.search(
                r"([\d,]+|[\u06f0-\u06f9,]+)\s*(تومان|تومانی|هزار|ریال)",
                text_content,
            )
        price = price_match.group(1).replace(",", "") if price_match else "None"

        if price != "None":
            price = self._convert_persian_nums(price)

        # 2. Regex for Likes OR Views (Videos show 'مشاهده' instead of 'لایک')
        likes_match = re.search(r"([\d۰-۹,]+)\s*(لایک|مشاهده)", text_content)
        likes = likes_match.group(1).replace(",", "") if likes_match else "0"
        likes = self._convert_persian_nums(likes)

        # 3. Regex for Comments (Safely defaults to 0 if not found)
        comments_match = re.search(r"([\d۰-۹,]+)\s*کامنت", text_content)
        comments = comments_match.group(1).replace(",", "") if comments_match else "0"
        comments = self._convert_persian_nums(comments)

        return {
            "price": price if price != "None" else "None",
            "likes": int(likes) if likes.isdigit() else 0,
            "comments": int(comments) if comments.isdigit() else 0,
        }

    def extract_single_post_data(self):
        """
        Extracts price/likes/comments for the SINGLE post currently open on screen.
        Intended to be called once per post, right after open_post_by_index(),
        since Rubika posts are standalone views (no joint scrollable feed).

        NOTE: verified against a real post page, the engagement info here does NOT
        live in a generic 'div[width=100%][display=flex]' container (that
        assumption was wrong and always returned no match). The like count
        renders as plain text like "<strong>0</strong> لایک", and the caption
        (containing the price as "قیمت 925") is a separate text block. Comment
        counts do not appear to render inline at all when zero, so this may
        legitimately return 0 comments for posts with no comments -- there is no
        separate confirmation step for that field.
        """
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        text_content = soup.get_text(separator=" ")
        return self._parse_engagement_text(text_content)

    def extract_post_data(self):
        """
        Extracts HTML from Selenium, parses it with BeautifulSoup,
        and extracts details using unified Regex tailored to handle both
        photo and video posts dynamically.

        NOTE: This assumes multiple post info blocks are simultaneously present
        in a single scrollable feed. If posts open as standalone pages (no joint
        feed), use open_post_by_index() + extract_single_post_data() in a loop
        instead.
        """
        print("[Scraper] Extracting DOM data using BeautifulSoup & Regex...")
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        products = []

        # Locate all primary containers. Both the photo and video HTML snippets
        # share this exact structural footprint.
        all_containers = soup.find_all(
            "div", attrs={"width": "100%", "display": "flex"}
        )

        valid_posts = []
        for container in all_containers:
            text = container.get_text()
            # A valid post must contain engagement metrics (Likes, Views, or Comments).
            # This filters out random UI elements like headers or navbars.
            if re.search(r"(لایک|مشاهده|کامنت)", text) and container not in valid_posts:
                valid_posts.append(container)

        print(f"[Scraper] Found {len(valid_posts)} structural post blocks.")

        for idx, post in enumerate(valid_posts):
            try:
                text_content = post.get_text(separator=" ")
                parsed = self._parse_engagement_text(text_content)
                parsed["post_index"] = idx + 1
                products.append(parsed)

            except Exception as e:
                print(f"[Warning] Error parsing item index {idx}: {str(e)}")
                continue

        return products

    def save_to_csv(self, product_list):
        """Writes data into a structured CSV file for downstream ML analysis."""
        with open(self.output_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["post_index", "price", "likes", "comments"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for product in product_list:
                writer.writerow(product)

        print(
            f"[Success] Extracted raw dataset successfully exported to {self.output_path}"
        )

    def _convert_persian_nums(self, text):
        """Helper utility converting Persian/Arabic digit characters to standard English integers."""
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        arabic_digits = "٠١٢٣٤٥٦٧٨٩"
        english_digits = "0123456789"

        translation_table = str.maketrans(
            persian_digits + arabic_digits, english_digits * 2
        )
        return text.translate(translation_table)

