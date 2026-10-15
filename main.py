"""Command-line entry point: fill the search form, scrape cars and vendors, save results."""

import argparse
from datetime import datetime

from export import save
from scraper import TiketCarRentalScraper


def main() -> None:
    p = argparse.ArgumentParser(description="Fill the tiket.com car rental search form.")
    p.add_argument("--rent-type", default="Dengan Sopir", choices=["Dengan Sopir", "Lepas Kunci"])
    p.add_argument("--location", required=True, help="Text to search, e.g. 'Jakarta'")
    p.add_argument("--pick", help="Exact suggestion title to choose, e.g. 'Jakarta Selatan' (default: first)")
    p.add_argument("--date", required=True, help="Pickup date, YYYY-MM-DD")
    p.add_argument("--time", required=True, help="Pickup time, HH:MM (24h)")
    p.add_argument("--days", type=int, default=1, help="Rental duration in days")
    p.add_argument("--headless", action="store_true")
    p.add_argument("--no-search", action="store_true", help="Fill the form but don't click 'Ayo cari'")
    p.add_argument("--output", help="Save results to a .json (nested) or .csv (one row per vendor) file")
    p.add_argument("--no-vendors", action="store_true", help="Skip opening each car's vendor panel (much faster)")
    p.add_argument("--max-cars", type=int, help="Only scrape the first N cars")
    args = p.parse_args()

    s = TiketCarRentalScraper(headless=args.headless)
    try:
        s.open()
        s.select_rent_type(args.rent_type)
        s.select_location(args.location, pick=args.pick)
        s.select_date(datetime.strptime(args.date, "%Y-%m-%d").date())
        s.select_time(args.time)
        s.select_duration(args.days)
        print("Form filled:", s.form_summary())
        if not args.no_search:
            s.search()
            print("Results page:", s.driver.current_url)
            cars = s.scrape_results(with_vendors=not args.no_vendors, max_cars=args.max_cars)
            print(f"\nScraped {len(cars)} cars:")
            for c in cars:
                print(f"\n{c['name']} | {c['koper'] or '-'} koper | {c['penumpang'] or '-'} penumpang"
                      f" | {c['transmission'] or '-'}")
                for v in c.get("vendors", []):
                    print(f"    {v['name']:<30} IDR {v['price']:>10,}/hari  {', '.join(v['facilities']) or '-'}")
            if args.output:
                save(cars, args.output)
                print(f"\nSaved to {args.output}")
        # input("Press Enter to close the browser...")
    finally:
        s.close()


if __name__ == "__main__":
    main()
