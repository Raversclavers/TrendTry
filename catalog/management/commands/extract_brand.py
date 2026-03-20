import json
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from catalog.models import Brand, Product, RawCrawl

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
        "faq": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                },
            },
        },
        "shipping_info": {"type": "string"},
        "product_description": {"type": "string"},
    },
    "required": [
        "brand_name",
        "product_name",
        "price",
        "currency",
    ],
}

REQUIRED_FIELDS = ["brand_name", "product_name", "price", "currency"]


class Command(BaseCommand):
    help = "Extract brand/product data from a URL using the Firecrawl extract API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            required=True,
            help="The brand's official product/collection page URL",
        )

    def handle(self, *args, **options):
        url = options["url"]
        api_key = getattr(settings, "FIRECRAWL_API_KEY", None) or ""
        if not api_key:
            raise CommandError(
                "FIRECRAWL_API_KEY is not set. Add it to your .env file."
            )

        domain = urlparse(url).netloc

        # ----- Call Firecrawl /v1/extract -----
        self.stdout.write(f"Extracting data from: {url}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "urls": [url],
            "prompt": (
                "Extract detailed product information including brand name, "
                "product name, category, price, currency, main marketing "
                "claims, ingredients or specs, size variants, image URLs, "
                "FAQ entries, shipping info, and product description."
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
            raise CommandError(
                f"Firecrawl API error {resp.status_code}: {resp.text[:500]}"
            )

        resp_json = resp.json()

        # The extract endpoint may return an async job — poll if needed
        if resp_json.get("success") and "id" in resp_json:
            resp_json = self._poll_for_result(resp_json["id"], headers)

        # ----- Store raw response -----
        RawCrawl.objects.create(
            brand_domain=domain,
            url=url,
            response=resp_json,
        )
        self.stdout.write(self.style.SUCCESS("Raw response saved to RawCrawl."))

        # ----- Parse extracted data -----
        data = resp_json.get("data", {})
        if isinstance(data, list):
            data = data[0] if data else {}

        missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
        if missing:
            raise CommandError(
                f"Firecrawl response missing required fields: {', '.join(missing)}. "
                f"Raw response saved for debugging."
            )

        # ----- Get or create Brand -----
        brand_name = data["brand_name"]
        category_raw = (data.get("category") or "gadgets").lower()
        valid_cats = {c.value for c in Brand.Category}
        category = category_raw if category_raw in valid_cats else "gadgets"

        brand, brand_created = Brand.objects.get_or_create(
            slug=slugify(brand_name),
            defaults={
                "name": brand_name,
                "domain": domain,
                "category": category,
            },
        )

        # ----- Get or create Product -----
        try:
            price = Decimal(str(data["price"]))
        except (InvalidOperation, TypeError, ValueError):
            price = Decimal("0.00")

        product_defaults = {
            "title": data["product_name"],
            "slug": slugify(data["product_name"]),
            "brand": brand,
            "price": price,
            "currency": (data.get("currency") or "USD")[:3],
            "image_url": (data.get("image_urls") or [""])[0],
            "main_claims": "\n".join(data.get("main_claims") or []),
            "specs": data.get("ingredients_or_specs") or {},
            "variants": data.get("size_variants") or [],
            "last_crawled": timezone.now(),
            "is_active": True,
        }

        product, product_created = Product.objects.get_or_create(
            source_url=url,
            defaults=product_defaults,
        )

        if not product_created:
            # Update existing record
            for field, value in product_defaults.items():
                setattr(product, field, value)
            product.save()

        # ----- Summary -----
        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("EXTRACTION COMPLETE"))
        self.stdout.write("=" * 50)
        self.stdout.write(
            f"Brand:   {brand.name} ({'CREATED' if brand_created else 'EXISTS'})"
        )
        self.stdout.write(
            f"Product: {product.title} ({'CREATED' if product_created else 'UPDATED'})"
        )
        self.stdout.write(f"Price:   {product.currency} {product.price}")
        self.stdout.write(f"Claims:  {len(data.get('main_claims') or [])} items")
        self.stdout.write(f"Specs:   {len(data.get('ingredients_or_specs') or {})} keys")
        self.stdout.write(f"Variants:{len(data.get('size_variants') or [])} items")
        self.stdout.write(f"Images:  {len(data.get('image_urls') or [])} URLs")
        self.stdout.write(f"FAQ:     {len(data.get('faq') or [])} entries")
        self.stdout.write("=" * 50)

    def _poll_for_result(self, job_id, headers):
        """Poll the Firecrawl extract endpoint until the job completes."""
        poll_url = f"{FIRECRAWL_EXTRACT_URL}/{job_id}"
        self.stdout.write(f"Job queued (id={job_id}), polling for results...")

        for attempt in range(30):
            time.sleep(2)
            resp = requests.get(poll_url, headers=headers, timeout=30)
            if resp.status_code != 200:
                raise CommandError(
                    f"Polling error {resp.status_code}: {resp.text[:500]}"
                )
            result = resp.json()
            status = result.get("status", "")
            if status == "completed":
                self.stdout.write(self.style.SUCCESS("Extraction complete."))
                return result
            if status == "failed":
                raise CommandError(f"Firecrawl job failed: {result}")
            self.stdout.write(f"  Status: {status} (attempt {attempt + 1}/30)")

        raise CommandError("Firecrawl job timed out after 60 seconds.")
