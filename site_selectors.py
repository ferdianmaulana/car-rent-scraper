"""Everything tied to tiket.com's page markup. When the site changes, fix it here."""

URL = "https://www.tiket.com/id-id/sewa-mobil"

# The calendar labels each day as e.g. "22 Oktober 2026 Kamis".
MONTHS_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

# Class names are CSS modules (e.g. "LocationPicker_location__CSOEZ"); the hash
# suffix changes between deploys, so match on the stable prefix only.
SEL = {
    "promo_close": "[class*='BaseModal-module__modal_wrapper'] button[class*='close_button']",
    "tab_buttons": "#coachmark-landing-step1 button",
    "location_input": "#coachmark-landing-step2 > div",
    "location_text": "#coachmark-landing-step2 [class*='LocationInput_text']",
    # Placeholder differs per tab ("Masukkan Lokasi Sewa..." vs "Masukkan nama kota").
    "location_search": "[class*='LocationPicker_search_box'] input",
    "location_item": "[class*='LocationPicker_location__']",
    "date_input": "[data-testid='search-form-date-input']",
    "day_cell": "span[aria-label][class*='Day_day_number']",
    "time_input":"[data-testid='search-form-time-input']",
    "time_segment": "[class*='TimePickerDesktop_time_segment']",
    "duration_input": "[data-testid='search-form-duration-input'] > div",
    "duration_item": "[class*='DurationList_duration_item']",
    "modal": "[class*='BaseModal_modal__']",
    "modal_close": "[data-testid='modal-close-button']",
    "search_button": "#coachmark-landing button[class*='SearchForm_search_button']",
    # Results page
    "car_card": "[data-testid='data-test-container'] [class*='FleetCard_card_wrapper']",
    "car_name": "[class*='FleetCard_title']",
    "car_capacity_item": "[class*='FleetCard_capacity_item']",
    # "Pilih Vendor" panel, opened by clicking a car card
    "vendor_panel_car_name": "[class*='VendorPageContent_header'] span",
    "vendor_card": "[data-testid='vendor-content-wrapper'] [class*='VendorCard_content']",
    "vendor_name": "[class*='VendorCard_body'] > span",
    "vendor_facility": "[class*='VendorCard_facility_text']",
    "vendor_price": "[class*='VendorCard_final_price'] span",
    "vendor_original_price": "[class*='VendorCard_strikethrough_price']",
}
