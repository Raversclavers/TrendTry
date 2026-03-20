"""
Fill meta_title, meta_description, og_image for Product, Comparison,
and UseCasePage rows that are missing SEO data, using Claude claude-sonnet-4-20250514.
"""

import json
import textwrap

import anthropic
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from catalog.models import Comparison, Product, UseCasePage


def _call_claude(prompt: str) -> dict:
    """Send a prompt to Claude and return parsed JSON."""
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


PRODUCT_PROMPT = textwrap.dedent("""\
    You are an SEO copywriter for a consumer-tech review site called TrendTry.
    Given the product info below, return ONLY a JSON object with these keys:
    - "meta_title": max 70 chars, include main keyword & brand.
    - "meta_description": max 160 chars, compelling, include a CTA keyword.
    - "og_image": leave as empty string "".

    Product:
    Title: {title}
    Brand: {brand}
    Price: {price} {currency}
    Main claims: {main_claims}
""")

COMPARISON_PROMPT = textwrap.dedent("""\
    You are an SEO copywriter for a consumer-tech review site called TrendTry.
    Given the comparison info below, return ONLY a JSON object with these keys:
    - "meta_title": max 70 chars, "A vs B" style, include year.
    - "meta_description": max 160 chars, highlight key differences.
    - "og_image": leave as empty string "".

    Comparison:
    Title: {title}
    Product A: {product_a}
    Product B: {product_b}
    Winner for: {winner_for}
""")

USECASE_PROMPT = textwrap.dedent("""\
    You are an SEO copywriter for a consumer-tech review site called TrendTry.
    Given the use-case page info below, return ONLY a JSON object with these keys:
    - "meta_title": max 70 chars, targeting the audience & budget.
    - "meta_description": max 160 chars, mention top picks count & budget.
    - "og_image": leave as empty string "".

    Use Case Page:
    Title: {title}
    Audience: {audience}
    Budget max: ${budget_max}
    Top picks count: {picks_count}
""")


class Command(BaseCommand):
    help = "Generate SEO meta fields using Claude claude-sonnet-4-20250514 for objects missing them."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            choices=["product", "comparison", "usecase", "all"],
            default="all",
            help="Which model(s) to generate SEO for (default: all).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Max items to process per model (default: 50).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without saving.",
        )

    def handle(self, *args, **options):
        if not settings.ANTHROPIC_API_KEY:
            raise CommandError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env file."
            )

        target = options["model"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        if target in ("product", "all"):
            self._process_products(limit, dry_run)
        if target in ("comparison", "all"):
            self._process_comparisons(limit, dry_run)
        if target in ("usecase", "all"):
            self._process_usecases(limit, dry_run)

    def _process_products(self, limit, dry_run):
        qs = Product.objects.filter(
            Q(meta_title="") | Q(meta_description="")
        ).select_related("brand")[:limit]
        self.stdout.write(f"Products to process: {len(qs)}")
        for p in qs:
            prompt = PRODUCT_PROMPT.format(
                title=p.title,
                brand=p.brand.name,
                price=p.price,
                currency=p.currency,
                main_claims=p.main_claims[:300],
            )
            try:
                data = _call_claude(prompt)
                if dry_run:
                    self.stdout.write(f"  [DRY] {p.title}: {data}")
                else:
                    p.meta_title = data.get("meta_title", "")[:70]
                    p.meta_description = data.get("meta_description", "")[:160]
                    p.og_image = data.get("og_image", "")
                    p.save(update_fields=["meta_title", "meta_description", "og_image"])
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {p.title}"))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"  ✗ {p.title}: {exc}"))

    def _process_comparisons(self, limit, dry_run):
        qs = Comparison.objects.filter(
            Q(meta_title="") | Q(meta_description="")
        ).select_related("product_a", "product_b")[:limit]
        self.stdout.write(f"Comparisons to process: {len(qs)}")
        for c in qs:
            prompt = COMPARISON_PROMPT.format(
                title=c.title,
                product_a=c.product_a.title,
                product_b=c.product_b.title,
                winner_for=c.winner_for[:300],
            )
            try:
                data = _call_claude(prompt)
                if dry_run:
                    self.stdout.write(f"  [DRY] {c.title}: {data}")
                else:
                    c.meta_title = data.get("meta_title", "")[:70]
                    c.meta_description = data.get("meta_description", "")[:160]
                    c.og_image = data.get("og_image", "")
                    c.save(update_fields=["meta_title", "meta_description", "og_image"])
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {c.title}"))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"  ✗ {c.title}: {exc}"))

    def _process_usecases(self, limit, dry_run):
        qs = UseCasePage.objects.filter(
            Q(meta_title="") | Q(meta_description="")
        )[:limit]
        self.stdout.write(f"UseCasePages to process: {len(qs)}")
        for u in qs:
            prompt = USECASE_PROMPT.format(
                title=u.title,
                audience=u.audience,
                budget_max=u.budget_max,
                picks_count=u.top_picks.count(),
            )
            try:
                data = _call_claude(prompt)
                if dry_run:
                    self.stdout.write(f"  [DRY] {u.title}: {data}")
                else:
                    u.meta_title = data.get("meta_title", "")[:70]
                    u.meta_description = data.get("meta_description", "")[:160]
                    u.og_image = data.get("og_image", "")
                    u.save(update_fields=["meta_title", "meta_description", "og_image"])
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {u.title}"))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"  ✗ {u.title}: {exc}"))
