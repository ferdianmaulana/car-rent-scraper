# car-rent-scraper

A small Selenium script that searches car rentals and saves what it finds.

You give it a location, date, time and rental duration. It fills in the search form the same way you would by hand, opens the results, and goes through every car on the page. For each car it records the luggage and passenger capacity and the transmission, then opens the "Pilih Vendor" panel to see which rental companies offer it, what facilities they include and how much they charge per day.

## Setup

You'll need Python 3.10 or newer and Google Chrome. You don't have to install ChromeDriver yourself; Selenium downloads a matching one the first time it runs.

```
python -m venv .venv
.venv\Scripts\activate          # on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```
python main.py --rent-type "Lepas Kunci" --location Jakarta --pick Jakarta --date 2026-11-20 --time 10:00 --days 2 --output results.json
```

A Chrome window opens and you can watch it work. It prints progress as it opens each car, then a summary like this:

```
Toyota Agya | 2 koper | 4 penumpang | Otomatis
    THE LUCKY                      IDR    272,000/hari  Air Mineral, Gratis Antar Jemput di Lokasi Vendor
    JAKARTA TRANSPORT              IDR    296,500/hari  -
    TRAC ASTRA                     IDR    350,000/hari  Sewa Tanpa Deposit, Gratis Antar Jemput di Lokasi Vendor, ...
```

### Options

| Option | Required | What it does |
|---|---|---|
| `--location` | yes | Text typed into the location search, e.g. `Jakarta` |
| `--date` | yes | Pickup date as `YYYY-MM-DD` |
| `--time` | yes | Pickup time as `HH:MM` (24-hour) |
| `--rent-type` | no | `Dengan Sopir` (with driver, the default) or `Lepas Kunci` (self-drive) |
| `--pick` | no | Which suggestion to choose, e.g. `"Jakarta Selatan"`. Without it, the first suggestion is used. |
| `--days` | no | Rental duration in days. Default is 1. |
| `--output` | no | Where to save the results. A `.csv` extension gives CSV; anything else gives JSON. |
| `--max-cars` | no | Only scrape the first N cars. Handy when you're testing something. |
| `--no-vendors` | no | Skip the vendor panels and just list the cars. Much faster. |
| `--no-search` | no | Fill in the form and stop there |
| `--headless` | no | Run Chrome without a window |

Use double quotes around values with spaces (`"Lepas Kunci"`), especially in Windows cmd, which doesn't understand single quotes.

## Output

JSON keeps the natural shape of the data: each car has a list of vendors, and each vendor has a list of facilities.

```json
{
  "name": "Toyota Agya",
  "koper": 2,
  "penumpang": 4,
  "transmission": "Otomatis",
  "vendors": [
    {
      "name": "THE LUCKY",
      "facilities": ["Air Mineral", "Gratis Antar Jemput di Lokasi Vendor"],
      "price": 272000,
      "original_price": 375000
    }
  ]
}
```

CSV has one row per car and vendor, so a car with four vendors takes four rows. The facilities column holds a JSON array (`["Air Mineral", "Car Charger"]`) because the number of facilities varies a lot between vendors. The file is written as UTF-8 with a BOM so Excel opens it without mangling the text.

Some things worth knowing about the data:

- Prices are per day, in rupiah, saved as plain numbers (`272000`, not `IDR 272.000`).
- `original_price` is the crossed-out price. It's only filled in when the vendor is showing a discount.
- `transmission` is always empty for "Dengan Sopir". The site simply doesn't show it for cars with a driver.
- The same model can show up twice, for example once as Manual and once as Otomatis. These are separate listings on the site.

## Things the site enforces

The script picks times with the site's own up/down buttons, so the site's booking rules still apply. If you ask for something the site won't allow, the script stops and tells you why. In practice:

- Pickup has to be at least 6 hours from now.
- Same-day bookings close at 14:00 WIB.
- Dates in the past are greyed out in the calendar.

## How long it takes

Opening each car's vendor panel takes a few seconds. A full run for Jakarta self-drive (28 cars) took a little under two minutes. With `--no-vendors` it's much quicker, since it only reads the results list.

## Project layout

```
main.py            command-line options, printing, saving
scraper.py         TiketCarRentalScraper: the form, results page and vendor panels
site_selectors.py  every CSS selector the scraper relies on
export.py          JSON and CSV writers
```

You can also use the scraper from your own code, for example to loop over several cities or dates:

```python
from datetime import date
from scraper import TiketCarRentalScraper
from export import save

s = TiketCarRentalScraper(headless=True)
try:
    s.open()
    s.select_rent_type("Lepas Kunci")
    s.select_location("Bandung")
    s.select_date(date(2026, 11, 20))
    s.select_time("10:00")
    s.select_duration(2)
    s.search()
    save(s.scrape_results(), "bandung.json")
finally:
    s.close()
```

## When it breaks

It will eventually, because the website changes its frontend from time to time. The class names on the page look like `FleetCard_title__moU8D`. The part after the double underscore changes on every deploy, which is why the selectors only match the beginning (`[class*='FleetCard_title']`). If the site renames a component outright, the fix is usually one line in `site_selectors.py`.

A good way to find the new name is to run with `--max-cars 1`, wait for it to fail, and inspect that part of the page in Chrome DevTools.

## A note on use

This is meant for personal research. Please keep runs reasonable, and check website's terms before using the data for anything commercial.
