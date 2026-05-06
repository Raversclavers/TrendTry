"""Use Firecrawl /v1/search to auto-find a real product page URL for every
Product whose source_url still points at a Google Shopping search.

Run before refresh_products so the scraper has authentic product pages to
extract og:image, price, and specs from instead of search-result pages.
"""

import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from catalog.models import Product

FIRECRAWL_SEARCH_URL = "https://api.firecrawl.dev/v1/search"

# Hosts whose product pages we trust to expose a real og:image. We pick the
# first result URL whose host matches one of these — skipping marketplaces
# that often redirect or paywall the page.
TRUSTED_HOSTS = (
    "amazon.com", "amazon.co.uk", "amazon.de",
    "bestbuy.com", "bhphotovideo.com", "adorama.com",
    "apple.com", "sony.com", "logitech.com", "elgato.com",
    "shure.com", "rode.com", "razer.com", "wooting.io",
    "keychron.com", "grovemade.com", "orbitkey.com", "benq.com",
    "dji.com", "insta360.com", "aputure.com", "anker.com",
    "us.govee.com", "govee.com", "nanoleaf.me",
    "newegg.com", "target.com", "walmart.com",
)


class Command(BaseCommand):
    help = (
        "Auto-discover a real product page URL for each Product whose "
        "source_url is still a Google Shopping search. Updates source_url "
        "in place — review in admin before running refresh_products."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max products to process (0 = all)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-discover even for products with non-Google source_url",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be updated without writing changes",
        )

    def handle(self, *args, **options):
        api_key = getattr(settings, "FIRECRAWL_API_KEY", None) or ""
        if not api_key:
            raise CommandError("FIRECRAWL_API_KEY is not set.")

        qs = Product.objects.select_related("brand").filter(is_active=True)
        if not options["force"]:
            qs = qs.filter(source_url__contains="google.com/search")
        if options["limit"]:
            qs = qs[: options["limit"]]

        products = list(qs)
        if not products:
            self.stdout.write("No products need source URL discovery.")
            return

        self.stdout.write(f"Discovering source URLs for {len(products)} product(s).\n")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        updated = skipped = failed = 0
        for i, product in enumerate(products, 1):
            close_old_connections()
            label = f"  [{i}/{len(products)}] {product.title}"
            try:
                url = self._search_for_product(product, headers)
                if not url:
                    self.stdout.write(self.style.WARNING(f"{label}\n    no trusted result"))
                    skipped += 1
                    continue
                if options["dry_run"]:
                    self.stdout.write(f"{label}\n    [DRY] {url}")
                else:
                    product.source_url = url
                    product.save(update_fields=["source_url"])
                    self.stdout.write(self.style.SUCCESS(f"{label}\n    -> {url}"))
                updated += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"{label}\n    FAILED: {exc}"))
                failed += 1
            time.sleep(1)  # respect free-plan rate limit (2 concurrent)

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("DISCOVERY COMPLETE"))
        self.stdout.write(f"  updated: {updated}, skipped: {skipped}, failed: {failed}")
        self.stdout.write("=" * 50)

    def _search_for_product(self, product, headers):
        """Return the first trusted-host URL for this product, or '' if none."""
        query = f"{product.brand.name} {product.title} buy"
        resp = requests.post(
            FIRECRAWL_SEARCH_URL,
            headers=headers,
            json={"query": query, "limit": 5},
            timeout=30,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"search API {resp.status_code}: {resp.text[:200]}")

        results = resp.json().get("data") or []
        # Prefer trusted hosts; fall back to first result if none match.
        for r in results:
            url = (r or {}).get("url", "")
            if any(host in url for host in TRUSTED_HOSTS):
                return url
        if results:
            first = (results[0] or {}).get("url", "")
            return first
        return ""
