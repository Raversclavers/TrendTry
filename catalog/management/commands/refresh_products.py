import json
import time
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Q
from django.utils import timezone

from catalog.models import Product, ProductChangeLog, RawCrawl

FIRECRAWL_EXTRACT_URL = "https://api.firecrawl.dev/v1/extract"
FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "brand_name": {"type": "string"},
        "product_name": {"type": "string"},
        "category": {"type": "string"},
        "price": {"type": "number"},
        "currency": {"type": "string"},
        "main_claims": {"type": "array", "items": {"type": "string"}},
        "ingredients_or_specs": {"type": "object"},
        "size_variants": {"type": "array", "items": {"type": "string"}},
        "image_urls": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["product_name", "price", "currency"],
}

# Fields to track for changes: (firecrawl_key, model_field, converter)
TRACKED_FIELDS = [
    ("price", "price", lambda v: str(Decimal(str(v)))),
    ("ingredients_or_specs", "specs", lambda v: json.dumps(v or {}, sort_keys=True)),
    ("main_claims", "main_claims", lambda v: "\n".join(v) if isinstance(v, list) else str(v or "")),
]


class Command(BaseCommand):
    help = "Re-crawl stale products via Firecrawl and log any changes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Re-crawl products older than this many days (default: 7)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max products to process (0 = all)",
        )
        parser.add_argument(
            "--images-only",
            action="store_true",
            help=(
                "Skip the expensive /extract call (LLM-based, ~5 credits) "
                "and only fetch og:image via /scrape (~1 credit per product)."
            ),
        )

    def handle(self, *args, **options):
        api_key = getattr(settings, "FIRECRAWL_API_KEY", None) or ""
        if not api_key:
            raise CommandError(
                "FIRECRAWL_API_KEY is not set. Add it to your .env file."
            )

        cutoff = timezone.now() - timedelta(days=options["days"])
        stale = Product.objects.filter(
            Q(last_crawled__isnull=True) | Q(last_crawled__lt=cutoff),
            is_active=True,
            source_url__gt="",
        ).order_by("last_crawled")

        if options["limit"]:
            stale = stale[: options["limit"]]

        products = list(stale)
        if not products:
            self.stdout.write("No stale products found.")
            return

        self.stdout.write(f"Found {len(products)} stale product(s) to refresh.\n")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        refreshed = 0
        total_changes = 0

        for product in products:
            self.stdout.write(f"  [{refreshed + 1}/{len(products)}] {product.title}")
            # Drop any DB connection killed by Railway's Postgres proxy idle
            # timeout during the previous Firecrawl poll. Django opens a
            # fresh one on the next query.
            connection.close()
            try:
                if options["images_only"]:
                    changes = self._refresh_image_only(product, headers)
                else:
                    changes = self._refresh_one(product, headers)
                refreshed += 1
                total_changes += changes
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"    FAILED: {exc}")
                )

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("REFRESH COMPLETE"))
        self.stdout.write(f"  {refreshed} products refreshed, {total_changes} changes detected")
        self.stdout.write("=" * 50)

    # ------------------------------------------------------------------

    def _refresh_one(self, product, headers):
        """Extract fresh data for a single product, diff, and update."""
        payload = {
            "urls": [product.source_url],
            "prompt": (
                "Extract product info: product name, price, currency, main "
                "marketing claims, ingredients or specs, size variants, AND "
                "all product image URLs visible on the page (full https:// "
                "URLs only — no relative paths, no data: URIs, no thumbnails). "
                "Prioritize the highest-resolution main product photo first "
                "in the image_urls list."
            ),
            "schema": EXTRACT_SCHEMA,
        }

        resp = requests.post(
            FIRECRAWL_EXTRACT_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"API {resp.status_code}: {resp.text[:200]}")

        resp_json = resp.json()

        # Handle async job polling — this blocks for up to 60s per product.
        # Railway's Postgres proxy will close any idle connection in that
        # window, so we drop the connection on the way out and let Django
        # open a fresh one for the writes below.
        if resp_json.get("success") and "id" in resp_json:
            resp_json = self._poll_for_result(resp_json["id"], headers)
            connection.close()

        # Save raw response
        domain = urlparse(product.source_url).netloc
        RawCrawl.objects.create(
            brand_domain=domain,
            url=product.source_url,
            response=resp_json,
        )

        data = resp_json.get("data", {})
        if isinstance(data, list):
            data = data[0] if data else {}

        # --- Diff tracked fields ---
        changes = 0
        for fc_key, model_field, converter in TRACKED_FIELDS:
            raw_new = data.get(fc_key)
            if raw_new is None:
                continue

            try:
                new_normalised = converter(raw_new)
            except (InvalidOperation, TypeError, ValueError):
                continue

            old_value = getattr(product, model_field)
            if model_field == "specs":
                old_normalised = json.dumps(old_value or {}, sort_keys=True)
            elif model_field == "price":
                old_normalised = str(old_value)
            else:
                old_normalised = str(old_value or "")

            if old_normalised != new_normalised:
                ProductChangeLog.objects.create(
                    product=product,
                    field_name=model_field,
                    old_value=old_normalised,
                    new_value=new_normalised,
                )
                self.stdout.write(
                    self.style.WARNING(f"    CHANGED: {model_field}")
                )
                changes += 1

                # Apply the new value to the product
                if model_field == "price":
                    product.price = Decimal(new_normalised)
                elif model_field == "specs":
                    product.specs = data.get(fc_key) or {}
                else:
                    product.main_claims = new_normalised

        # --- Image: prefer og:image from /scrape (social-share image, the
        # highest-quality main product photo), fall back to the first valid
        # http(s) URL from /extract's image_urls.
        new_image = self._fetch_og_image(product.source_url, headers)
        if not new_image:
            image_urls = data.get("image_urls") or []
            if isinstance(image_urls, list):
                for url in image_urls:
                    if isinstance(url, str) and url.startswith(("http://", "https://")):
                        new_image = url
                        break
        if new_image and new_image != product.image_url:
            ProductChangeLog.objects.create(
                product=product,
                field_name="image_url",
                old_value=product.image_url or "",
                new_value=new_image,
            )
            product.image_url = new_image
            self.stdout.write(self.style.WARNING("    CHANGED: image_url"))
            changes += 1

        product.last_crawled = timezone.now()
        product.save()

        if changes == 0:
            self.stdout.write(self.style.SUCCESS("    No changes"))
        return changes

    def _refresh_image_only(self, product, headers):
        """Cheap path: only fetch og:image via /scrape, skip /extract entirely.

        Costs ~1 Firecrawl credit per product instead of ~5.
        """
        new_image = self._fetch_og_image(product.source_url, headers)
        connection.close()
        if not new_image:
            self.stdout.write(self.style.WARNING("    no og:image"))
            product.last_crawled = timezone.now()
            product.save(update_fields=["last_crawled"])
            return 0
        if new_image == product.image_url:
            self.stdout.write(self.style.SUCCESS("    No changes"))
            product.last_crawled = timezone.now()
            product.save(update_fields=["last_crawled"])
            return 0
        ProductChangeLog.objects.create(
            product=product,
            field_name="image_url",
            old_value=product.image_url or "",
            new_value=new_image,
        )
        product.image_url = new_image
        product.last_crawled = timezone.now()
        product.save(update_fields=["image_url", "last_crawled"])
        self.stdout.write(self.style.WARNING("    CHANGED: image_url"))
        return 1

    def _fetch_og_image(self, url, headers):
        """Use Firecrawl /scrape to grab the page's og:image — the canonical
        social-share photo, almost always the main product image.

        Returns a https URL or '' if nothing usable was found.
        """
        try:
            resp = requests.post(
                FIRECRAWL_SCRAPE_URL,
                headers=headers,
                json={
                    "url": url,
                    "formats": ["markdown"],
                    "onlyMainContent": False,
                },
                timeout=45,
            )
            if resp.status_code != 200:
                return ""
            meta = (resp.json().get("data") or {}).get("metadata") or {}
            for key in ("ogImage", "og:image", "image", "twitterImage"):
                v = meta.get(key)
                if isinstance(v, str) and v.startswith(("http://", "https://")):
                    return v
        except requests.RequestException:
            pass
        return ""

    def _poll_for_result(self, job_id, headers):
        """Poll the Firecrawl extract endpoint until the job completes."""
        poll_url = f"{FIRECRAWL_EXTRACT_URL}/{job_id}"
        self.stdout.write(f"    Polling job {job_id}...")

        for _ in range(30):
            time.sleep(2)
            resp = requests.get(poll_url, headers=headers, timeout=30)
            if resp.status_code != 200:
                continue
            result = resp.json()
            if result.get("status") == "completed":
                return result
        raise RuntimeError(f"Job {job_id} timed out after 60 s")
