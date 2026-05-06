import json
import time
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from catalog.models import Product, ProductChangeLog, RawCrawl

FIRECRAWL_EXTRACT_URL = "https://api.firecrawl.dev/v1/extract"

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
            try:
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
                "Extract product information: product name, price, currency, "
                "main marketing claims, ingredients or specs, and size variants."
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

        # Handle async job polling
        if resp_json.get("success") and "id" in resp_json:
            resp_json = self._poll_for_result(resp_json["id"], headers)

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

        # --- Image: take the first valid http(s) URL from image_urls ---
        image_urls = data.get("image_urls") or []
        if isinstance(image_urls, list):
            for url in image_urls:
                if isinstance(url, str) and url.startswith(("http://", "https://")):
                    if url != product.image_url:
                        ProductChangeLog.objects.create(
                            product=product,
                            field_name="image_url",
                            old_value=product.image_url or "",
                            new_value=url,
                        )
                        product.image_url = url
                        self.stdout.write(self.style.WARNING("    CHANGED: image_url"))
                        changes += 1
                    break

        product.last_crawled = timezone.now()
        product.save()

        if changes == 0:
            self.stdout.write(self.style.SUCCESS("    No changes"))
        return changes

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
