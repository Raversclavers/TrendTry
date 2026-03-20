"""Populate database with realistic seed data for desk accessories & tech gadgets."""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from catalog.models import (
    AffiliateLink,
    Brand,
    Comparison,
    Product,
    TrendEntry,
    UseCasePage,
)

BRANDS = [
    {
        "name": "Grovemade",
        "domain": "grovemade.com",
        "category": "accessories",
        "logo_url": "",
    },
    {
        "name": "Keychron",
        "domain": "keychron.com",
        "category": "gadgets",
        "logo_url": "",
    },
    {
        "name": "Orbitkey",
        "domain": "orbitkey.com",
        "category": "accessories",
        "logo_url": "",
    },
    {
        "name": "BenQ",
        "domain": "benq.com",
        "category": "gadgets",
        "logo_url": "",
    },
]

PRODUCTS = [
    {
        "brand": "Grovemade",
        "title": "Grovemade Wood Desk Shelf",
        "price": Decimal("220.00"),
        "source_url": "https://grovemade.com/product/wood-desk-shelf/",
        "image_url": "https://grovemade.com/media/catalog/product/d/e/desk-shelf-walnut-galA-C1_2.jpg",
        "main_claims": "Handcrafted solid hardwood desk shelf\nElevates monitor to ergonomic height\nCable management channel built in\nSustainably sourced American hardwood",
        "specs": {"material": "Walnut / Maple hardwood", "dimensions": "32 x 10.5 x 4 inches", "weight": "6.5 lbs", "finish": "Natural oil"},
        "variants": ["Walnut", "Maple"],
    },
    {
        "brand": "Grovemade",
        "title": "Grovemade Leather Desk Pad",
        "price": Decimal("120.00"),
        "source_url": "https://grovemade.com/product/matte-desk-pad/",
        "image_url": "https://grovemade.com/media/catalog/product/d/e/desk-pad-leather-galA_2.jpg",
        "main_claims": "Premium vegetable-tanned leather\nLarge work surface 27.5 x 17.5 inches\nDevelops rich patina over time\nNon-slip cork base",
        "specs": {"material": "Vegetable-tanned leather + cork base", "dimensions": "27.5 x 17.5 x 0.2 inches", "colors": "Natural, Black, Brown"},
        "variants": ["Small", "Large", "Extra Large"],
    },
    {
        "brand": "Keychron",
        "title": "Keychron K2 HE Wireless Mechanical Keyboard",
        "price": Decimal("109.99"),
        "source_url": "https://www.keychron.com/products/keychron-k2-he-wireless-mechanical-keyboard",
        "image_url": "https://cdn.shopify.com/s/files/1/0059/0630/1017/files/Keychron-K2-HE.jpg",
        "main_claims": "Hall Effect magnetic switches with adjustable actuation\n75% compact layout perfect for creators\nBluetooth 5.1 + 2.4GHz + USB-C triple connectivity\nUp to 200 hours battery life",
        "specs": {"layout": "75% (84 keys)", "switches": "Gateron Double-Rail Magnetic", "connectivity": "Bluetooth 5.1 / 2.4GHz / USB-C", "battery": "4000mAh", "backlight": "South-facing RGB"},
        "variants": ["Carbon Black", "Shell White"],
    },
    {
        "brand": "Keychron",
        "title": "Keychron Q1 HE Wireless QMK Keyboard",
        "price": Decimal("219.99"),
        "source_url": "https://www.keychron.com/products/keychron-q1-he-wireless-qmk-custom-mechanical-keyboard",
        "image_url": "https://cdn.shopify.com/s/files/1/0059/0630/1017/files/Keychron-Q1-HE.jpg",
        "main_claims": "Full aluminum CNC-machined body\nQMK/VIA programmable with magnetic switches\nGasket mount design for premium typing feel\nPerfect for content creators and developers",
        "specs": {"layout": "75% (82 keys)", "case": "6063 Aluminum CNC", "mount": "Gasket", "switches": "Gateron Double-Rail Magnetic", "weight": "3.95 lbs"},
        "variants": ["Carbon Black", "Shell White", "Navy Blue"],
    },
    {
        "brand": "Orbitkey",
        "title": "Orbitkey Desk Mat",
        "price": Decimal("64.90"),
        "source_url": "https://www.orbitkey.com/collections/desk-mat/products/desk-mat",
        "image_url": "https://cdn.shopify.com/s/files/1/0266/5065/8583/products/orbitkey-desk-mat.jpg",
        "main_claims": "Vegan leather desk mat with magnetic cable holder\nDocument hideaway pocket underneath\nEasy-clean stain-resistant surface\nMinimalist design fits any setup",
        "specs": {"material": "Vegan leather + recycled PET felt base", "dimensions": "Medium: 68 x 32cm, Large: 84 x 36cm", "features": "Magnetic cable holder, document pocket"},
        "variants": ["Stone Grey", "Black", "Navy"],
    },
    {
        "brand": "BenQ",
        "title": "BenQ ScreenBar Halo Monitor Light",
        "price": Decimal("179.00"),
        "source_url": "https://www.benq.com/en-us/lighting/monitor-light/screenbar-halo.html",
        "image_url": "https://www.benq.com/content/dam/benq/lighting/screenbar-halo/gallery/screenbar-halo-hero.jpg",
        "main_claims": "Asymmetric light that illuminates desk without screen glare\nWireless controller with ambient light sensor\nBack-light for immersive glow effect\nAuto-dimming adapts to environment",
        "specs": {"power": "USB-powered (5V 1A)", "color_temp": "2700K-6500K", "luminance": "500 lux at 45cm", "controller": "Wireless dial with ambient sensor"},
        "variants": [],
    },
    {
        "brand": "BenQ",
        "title": "BenQ ScreenBar Pro Monitor Light",
        "price": Decimal("149.00"),
        "source_url": "https://www.benq.com/en-us/lighting/monitor-light/screenbar-pro.html",
        "image_url": "https://www.benq.com/content/dam/benq/lighting/screenbar-pro/gallery/screenbar-pro-hero.jpg",
        "main_claims": "Built-in proximity sensor auto on/off\n16 preset lighting modes\nNo desk space required - clips onto monitor\nFlicker-free & blue light safe",
        "specs": {"power": "USB-powered (5V 1.3A)", "color_temp": "2700K-6500K", "luminance": "530 lux at 45cm", "features": "Proximity sensor, 16 presets"},
        "variants": [],
    },
]

TRENDS = [
    {
        "product": "Keychron K2 HE Wireless Mechanical Keyboard",
        "why_trending": "Hall Effect magnetic switches are the biggest keyboard trend of 2025. Creators love the adjustable actuation points for both gaming and typing. The K2 HE offers this tech at an accessible price point.",
        "creator_hooks": ["Adjustable actuation for different tasks", "Clean aesthetic for desk setups", "Triple connectivity for multi-device workflows"],
        "platform_fit": ["youtube", "tiktok", "instagram"],
        "trend_score": 9,
    },
    {
        "product": "BenQ ScreenBar Halo Monitor Light",
        "why_trending": "Desk lighting has become essential content for creators. The Halo's back-light feature creates the ambient glow effect that performs extremely well in setup videos and TikTok desk tours.",
        "creator_hooks": ["Perfect for desk setup videos", "Back-glow creates viral aesthetics", "Practical upgrade every creator needs"],
        "platform_fit": ["youtube", "tiktok", "instagram"],
        "trend_score": 8,
    },
    {
        "product": "Grovemade Wood Desk Shelf",
        "why_trending": "The premium handcrafted aesthetic is dominating desk setup content. Grovemade's shelf elevates any setup from basic to aspirational. Major creator accounts are featuring it in 2025 desk tours.",
        "creator_hooks": ["Premium look for setup content", "Practical cable management", "Pairs with any desk setup theme"],
        "platform_fit": ["youtube", "instagram"],
        "trend_score": 7,
    },
    {
        "product": "Orbitkey Desk Mat",
        "why_trending": "Minimalist desk mats with hidden features are trending. The document pocket and magnetic cable holder hit the 'functional minimalism' trend perfectly.",
        "creator_hooks": ["Hidden features surprise viewers", "Clean minimalist look", "Budget-friendly upgrade"],
        "platform_fit": ["tiktok", "youtube"],
        "trend_score": 7,
    },
    {
        "product": "Keychron Q1 HE Wireless QMK Keyboard",
        "why_trending": "Premium Hall Effect keyboard with full customization. The aluminum build and gasket mount appeal to creators who want the best typing experience on camera.",
        "creator_hooks": ["Premium thock sound for ASMR content", "Fully customizable via QMK/VIA", "Content-worthy aluminum design"],
        "platform_fit": ["youtube", "tiktok"],
        "trend_score": 8,
    },
]

COMPARISONS = [
    {
        "title": "Keychron K2 HE vs Q1 HE: Best Hall Effect Keyboard for Creators",
        "product_a": "Keychron K2 HE Wireless Mechanical Keyboard",
        "product_b": "Keychron Q1 HE Wireless QMK Keyboard",
        "pros_a": "More affordable at $109.99\nSlimmer plastic build is lighter and more portable\nSame Hall Effect switch technology\n200-hour battery life",
        "cons_a": "Plastic case lacks premium feel\nNot QMK/VIA programmable\nLess dampening without gasket mount",
        "pros_b": "Full aluminum CNC body feels premium\nQMK/VIA fully programmable\nGasket mount for superior typing feel\nHeavier and more stable on desk",
        "cons_b": "Double the price at $219.99\nHeavier — less portable\nMore complex to customize out of the box",
        "winner_for": "Choose the K2 HE if you want excellent Hall Effect tech at a great price. Choose the Q1 HE if you're a creator who wants the premium keyboard that looks and sounds amazing in content.",
    },
    {
        "title": "BenQ ScreenBar Halo vs Pro: Which Monitor Light Should Creators Buy?",
        "product_a": "BenQ ScreenBar Halo Monitor Light",
        "product_b": "BenQ ScreenBar Pro Monitor Light",
        "pros_a": "Wireless dial controller feels premium\nBack-light illumination for ambient effects\nAmbient light sensor auto-adjusts\nPerfect for content creation backdrops",
        "cons_a": "$30 more expensive than Pro\nController needs AAA batteries\nSlightly lower max luminance",
        "pros_b": "Built-in proximity sensor (auto on/off)\n16 preset lighting modes\nHigher max luminance at 530 lux\nMore affordable at $149",
        "cons_b": "No wireless controller\nNo back-light ambient effect\nTouch controls on the bar itself",
        "winner_for": "The Halo is best for creators who want that ambient back-glow for setup videos. The Pro is better for pure productivity with its proximity sensor and stronger light output.",
    },
]

USECASES = [
    {
        "title": "Best Desk Accessories for YouTube Creators Under $300",
        "audience": "YouTube creators building an aesthetic desk setup",
        "budget_max": 300,
        "top_pick_titles": [
            "BenQ ScreenBar Halo Monitor Light",
            "Keychron K2 HE Wireless Mechanical Keyboard",
            "Orbitkey Desk Mat",
        ],
        "cautions": "Avoid cheap LED desk bars from unknown brands — inconsistent color temperature ruins video quality. Stick with known brands that offer flicker-free lighting.",
    },
    {
        "title": "Essential Tech Gadgets for Content Creators in 2025",
        "audience": "Full-time content creators upgrading their workspace",
        "budget_max": 500,
        "top_pick_titles": [
            "Keychron Q1 HE Wireless QMK Keyboard",
            "BenQ ScreenBar Halo Monitor Light",
            "Grovemade Wood Desk Shelf",
            "Grovemade Leather Desk Pad",
        ],
        "cautions": "Premium accessories add up fast. Prioritize lighting and keyboard first — they have the biggest impact on both your workflow and content quality.",
    },
]


class Command(BaseCommand):
    help = "Populate database with realistic seed data for desk accessories & tech gadgets"

    def handle(self, *args, **options):
        # Brands
        brands = {}
        for b in BRANDS:
            obj, created = Brand.objects.get_or_create(
                slug=slugify(b["name"]),
                defaults={
                    "name": b["name"],
                    "domain": b["domain"],
                    "category": b["category"],
                    "logo_url": b["logo_url"],
                },
            )
            brands[b["name"]] = obj
            self.stdout.write(f"  Brand: {obj.name} ({'created' if created else 'exists'})")

        # Products
        products = {}
        for p in PRODUCTS:
            brand = brands[p["brand"]]
            obj, created = Product.objects.get_or_create(
                slug=slugify(p["title"]),
                defaults={
                    "title": p["title"],
                    "brand": brand,
                    "price": p["price"],
                    "currency": "USD",
                    "source_url": p["source_url"],
                    "image_url": p["image_url"],
                    "main_claims": p["main_claims"],
                    "specs": p["specs"],
                    "variants": p["variants"],
                    "last_crawled": timezone.now(),
                    "is_active": True,
                },
            )
            products[p["title"]] = obj
            self.stdout.write(f"  Product: {obj.title} ({'created' if created else 'exists'})")

        # Trend entries
        for t in TRENDS:
            product = products[t["product"]]
            obj, created = TrendEntry.objects.get_or_create(
                product=product,
                defaults={
                    "why_trending": t["why_trending"],
                    "creator_hooks": t["creator_hooks"],
                    "platform_fit": t["platform_fit"],
                    "trend_score": t["trend_score"],
                },
            )
            self.stdout.write(f"  Trend: {product.title} ({obj.trend_score}/10) ({'created' if created else 'exists'})")

        # Comparisons
        for c in COMPARISONS:
            obj, created = Comparison.objects.get_or_create(
                slug=slugify(c["title"])[:255],
                defaults={
                    "title": c["title"],
                    "product_a": products[c["product_a"]],
                    "product_b": products[c["product_b"]],
                    "pros_a": c["pros_a"],
                    "cons_a": c["cons_a"],
                    "pros_b": c["pros_b"],
                    "cons_b": c["cons_b"],
                    "winner_for": c["winner_for"],
                },
            )
            self.stdout.write(f"  Comparison: {obj.title} ({'created' if created else 'exists'})")

        # Use case pages
        for u in USECASES:
            obj, created = UseCasePage.objects.get_or_create(
                slug=slugify(u["title"])[:255],
                defaults={
                    "title": u["title"],
                    "audience": u["audience"],
                    "budget_max": u["budget_max"],
                    "cautions": u["cautions"],
                },
            )
            if created:
                for title in u["top_pick_titles"]:
                    if title in products:
                        obj.top_picks.add(products[title])
            self.stdout.write(f"  UseCase: {obj.title} ({'created' if created else 'exists'})")

        # Affiliate links (placeholder URLs — replace with real affiliate URLs)
        for product in products.values():
            _, created = AffiliateLink.objects.get_or_create(
                product=product,
                defaults={
                    "network_name": "Direct",
                    "affiliate_url": product.source_url,
                },
            )
            if created:
                self.stdout.write(f"  AffiliateLink: {product.title}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seed data populated successfully!"))
        self.stdout.write(f"  Brands: {Brand.objects.count()}")
        self.stdout.write(f"  Products: {Product.objects.count()}")
        self.stdout.write(f"  Trends: {TrendEntry.objects.count()}")
        self.stdout.write(f"  Comparisons: {Comparison.objects.count()}")
        self.stdout.write(f"  Use Cases: {UseCasePage.objects.count()}")
        self.stdout.write(f"  Affiliate Links: {AffiliateLink.objects.count()}")
