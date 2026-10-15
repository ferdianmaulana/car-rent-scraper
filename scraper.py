"""Selenium scraper for tiket.com car rental (https://www.tiket.com/id-id/sewa-mobil).

Step 1: fill in the search form (rent type, location, date, time, duration) and submit.
Step 2: scrape each car on the results page (name, koper, penumpang, transmission).
Step 3: open each car's "Pilih Vendor" panel (rental company, facilities, price).
"""

import time
from datetime import date

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from site_selectors import MONTHS_ID, SEL, URL


def _idr_to_int(text: str) -> int:
    """'IDR 272.000' -> 272000"""
    return int("".join(ch for ch in text if ch.isdigit()))


class TiketCarRentalScraper:
    def __init__(self, headless: bool = False, timeout: int = 15):
        opts = webdriver.ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1400,1000")
        opts.add_argument("--lang=id-ID")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Chrome(options=opts)
        self.wait = WebDriverWait(self.driver, timeout)

    # ------------------------------------------------------------------ helpers
    def _find(self, css: str) -> WebElement:
        return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))

    def _visible(self, css: str) -> list[WebElement]:
        visible = []
        for e in self.driver.find_elements(By.CSS_SELECTOR, css):
            try:
                if e.is_displayed():
                    visible.append(e)
            except StaleElementReferenceException:
                pass  # React removed it between find and check (e.g. a closing modal)
        return visible

    def _click(self, el: WebElement) -> None:
        # JS click sidesteps the sticky promo banners that intercept native clicks.
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", el)

    def _click_button_with_text(self, text: str) -> None:
        btn = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//button[normalize-space(.)='{text}']")))
        self._click(btn)

    def _wait_modal_closed(self) -> None:
        try:
            WebDriverWait(self.driver, 5).until(lambda d: not self._visible(SEL["modal"]))
        except TimeoutException:
            pass

    # ------------------------------------------------------------------ steps
    def open(self) -> None:
        self.driver.get(URL)
        self._find(SEL["location_input"])
        time.sleep(3)  # promo popup and coachmark appear shortly after load
        self.dismiss_popups()

    def dismiss_popups(self) -> None:
        for el in self.driver.find_elements(By.CSS_SELECTOR, SEL["promo_close"]):
            self._click(el)
        # Onboarding coachmark ("Pilih tipe sewa mobil ... Lewati / Lanjut").
        for el in self.driver.find_elements(By.XPATH, "//*[normalize-space(text())='Lewati']"):
            self._click(el)

    def select_rent_type(self, rent_type: str) -> None:
        """rent_type: 'Dengan Sopir' (with driver) or 'Lepas Kunci' (self-drive)."""
        for btn in self.driver.find_elements(By.CSS_SELECTOR, SEL["tab_buttons"]):
            if btn.text.strip().lower() == rent_type.lower():
                self._click(btn)
                return
        raise ValueError(f"Rent type {rent_type!r} not found")

    def select_location(self, query: str, pick: str | None = None, landmark: str | None = None) -> str:
        """Search for `query` and pick the suggestion whose title equals `pick`
        (case-insensitive), or the first suggestion if `pick` is None."""
        self._click(self._find(SEL["location_input"]))
        box = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, SEL["location_search"])))
        box.clear()
        box.send_keys(query)

        # Suggestions refresh asynchronously; wait until they reflect the query.
        self.wait.until(lambda d: any(
            query.lower() in e.text.lower() for e in self._visible(SEL["location_item"])))
        items = self._visible(SEL["location_item"])
        titles = [i.find_element(By.CSS_SELECTOR, "[class*='List_title']").text.strip() for i in items]

        if pick is None:
            idx = 0
        else:
            matches = [n for n, t in enumerate(titles) if t.lower() == pick.lower()]
            if not matches:
                raise ValueError(f"Location {pick!r} not in suggestions: {titles}")
            idx = matches[0]
        self._click(items[idx])

        # "Dengan Sopir" opens a map dialog to confirm the pickup point;
        # "Lepas Kunci" is city-level and closes the picker straight away.
        confirm_xpath = "//button[normalize-space(.)='Atur Lokasi Jemput']"
        try:
            confirm = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, confirm_xpath)))
        except TimeoutException:
            confirm = None
        if confirm:
            if landmark:
                self.driver.find_element(By.CSS_SELECTOR, "input[placeholder^='Patokan']").send_keys(landmark)
            self._click(confirm)
        self._wait_modal_closed()
        return self._find(SEL["location_text"]).text.strip()

    def select_date(self, day: date) -> None:
        self._click(self._find(SEL["date_input"]))
        label = f"{day.day} {MONTHS_ID[day.month - 1]} {day.year} "
        cell_css = f"span[aria-label^='{label}']"
        # Day cells render ~0.5s after the modal opens.
        self.wait.until(lambda d: self._visible(SEL["day_cell"]))

        for _ in range(13):  # the calendar shows two months; page forward if needed
            cells = self._visible(cell_css)
            if cells:
                btn = cells[0].find_element(By.XPATH, "./ancestor::button[1]")
                if btn.get_attribute("disabled") is not None or "disabled" in (btn.get_attribute("class") or ""):
                    raise ValueError(f"Date {day} is not selectable")
                self._click(btn)
                self._wait_modal_closed()
                return
            nxt = self._visible("[aria-label='Bulan berikutnya']")
            if not nxt:
                break
            first_day = self._visible(SEL["day_cell"])[0].get_attribute("aria-label")
            self._click(nxt[0])
            self.wait.until(lambda d: (cells := self._visible(SEL["day_cell"]))
                            and cells[0].get_attribute("aria-label") != first_day)
        raise ValueError(f"Date {day} not found in calendar")

    def select_time(self, hhmm: str) -> None:
        """Set pickup time, e.g. '09:00'. Uses the up/down spin buttons so the
        site's own constraints (min lead time, minute step) are respected."""
        hour, minute = (int(x) for x in hhmm.split(":"))
        if not self._visible(SEL["time_segment"]):
            self._click(self._find(SEL["time_input"]))
        self.wait.until(lambda d: len(self._visible(SEL["time_segment"])) == 2)

        for seg_idx, target in ((0, hour), (1, minute)):
            for _ in range(60):
                seg = self._visible(SEL["time_segment"])[seg_idx]
                current = int(seg.find_element(By.TAG_NAME, "input").get_attribute("value"))
                if current == target:
                    break
                up, down = seg.find_elements(By.TAG_NAME, "button")
                btn = up if target > current else down
                if btn.get_attribute("disabled") is not None:
                    raise ValueError(f"Time {hhmm} is not available (stuck at {current:02d})")
                self._click(btn)
                time.sleep(0.15)
            else:
                raise ValueError(f"Could not reach {hhmm}; site may use a different minute step")

        self._click_button_with_text("Simpan")
        self._wait_modal_closed()

    def select_duration(self, days: int) -> None:
        self._click(self._find(SEL["duration_input"]))
        self.wait.until(lambda d: self._visible(SEL["duration_item"]))
        wanted = f"{days} hari"
        for item in self._visible(SEL["duration_item"]):
            if item.find_element(By.CSS_SELECTOR, "[class*='List_title']").text.strip() == wanted:
                self._click(item)
                self._wait_modal_closed()
                return
        raise ValueError(f"Duration {wanted!r} not offered")

    def form_summary(self) -> dict:
        form = self._find("#coachmark-landing")
        return {
            "location": form.find_element(By.CSS_SELECTOR, "[class*='LocationInput_text']").text.strip(),
            "date": form.find_element(By.CSS_SELECTOR, SEL["date_input"]).text.strip(),
            "time": form.find_element(By.CSS_SELECTOR, SEL["time_input"]).text.strip(),
            "duration": form.find_element(By.CSS_SELECTOR, "#coachmark-landing-step4 [class*='text_trunc']").text.strip(),
            "ends": " ".join(form.find_element(By.CSS_SELECTOR, "[class*='DurationInput_description_label']").text.split()),
        }

    def search(self) -> None:
        self._click(self._find(SEL["search_button"]))
        self.wait.until(EC.url_contains("/sewa-mobil/cari"))

    def scrape_results(self, with_vendors: bool = True, max_cars: int | None = None) -> list[dict]:
        """Read every car card on the results page.

        Each card lists capacity items like "2 koper", "4 penumpang" and, for
        "Lepas Kunci" only, a transmission ("Otomatis" / "Manual"). "Dengan
        Sopir" cards have no transmission, so that field is None for them.

        With `with_vendors`, each card is also clicked to open its "Pilih Vendor"
        panel, and the rental companies offering that car are added as `vendors`.
        """
        try:
            self.wait.until(lambda d: self._visible(SEL["car_card"]))
        except TimeoutException:
            return []  # no cars available for this search
        # Cards can arrive in batches; wait until the count stops changing.
        count = -1
        while count != len(self._visible(SEL["car_card"])):
            count = len(self._visible(SEL["car_card"]))
            time.sleep(1)
        self.dismiss_popups()  # the promo popup shows up on this page too

        total = min(count, max_cars) if max_cars else count
        cars = []
        for i in range(total):
            # Re-find the cards every time: opening/closing the panel can re-render them.
            car = self._parse_car(self._visible(SEL["car_card"])[i])
            if with_vendors:
                print(f"  [{i + 1}/{total}] {car['name']}", flush=True)
                car["vendors"] = self._scrape_vendors(i, car["name"])
            cars.append(car)
        return cars

    def _parse_car(self, card: WebElement) -> dict:
        car = {"name": card.find_element(By.CSS_SELECTOR, SEL["car_name"]).text.strip(),
               "koper": None, "penumpang": None, "transmission": None}
        for item in card.find_elements(By.CSS_SELECTOR, SEL["car_capacity_item"]):
            text = item.text.strip()
            value, _, unit = text.partition(" ")
            if unit == "koper":
                car["koper"] = int(value)
            elif unit == "penumpang":
                car["penumpang"] = int(value)
            elif text:
                car["transmission"] = text
        return car

    def _scrape_vendors(self, card_index: int, car_name: str) -> list[dict]:
        self._click(self._visible(SEL["car_card"])[card_index])
        # Make sure the panel shows this car, not the previous one still on screen.
        self.wait.until(lambda d: (h := self._visible(SEL["vendor_panel_car_name"]))
                        and h[0].text.strip() == car_name and self._visible(SEL["vendor_card"]))

        vendors = []
        for v in self._visible(SEL["vendor_card"]):
            original = v.find_elements(By.CSS_SELECTOR, SEL["vendor_original_price"])
            vendors.append({
                "name": v.find_element(By.CSS_SELECTOR, SEL["vendor_name"]).text.strip(),
                "facilities": [f.text.strip() for f in v.find_elements(By.CSS_SELECTOR, SEL["vendor_facility"])],
                "price": _idr_to_int(v.find_element(By.CSS_SELECTOR, SEL["vendor_price"]).text),
                # Only present when the vendor shows a discount.
                "original_price": _idr_to_int(original[0].text) if original else None,
            })

        for btn in self._visible(SEL["modal_close"]):
            self._click(btn)
        self._wait_modal_closed()
        return vendors

    def close(self) -> None:
        self.driver.quit()
