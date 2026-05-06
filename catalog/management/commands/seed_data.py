"""Populate database with realistic 2026 creator gear data.

Run: python manage.py seed_data

Idempotent — safe to re-run. Products use update_or_create so image URLs
and prices stay fresh; brands/trends/comparisons/usecases use get_or_create
so manual edits in admin are preserved.
"""

import os
from decimal import Decimal
from urllib.parse import quote_plus

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

# Brand color palette for placeholder images — matches each brand's
# recognizable colors so cards look intentional rather than generic.
BRAND_COLORS = {
    "Grovemade": ("3d2817", "f5e6d3"),
    "Keychron": ("1a1a1a", "f7c948"),
    "Orbitkey": ("2c3e50", "ecf0f1"),
    "BenQ": ("6c2bd9", "ffffff"),
    "Logitech": ("00b8fc", "ffffff"),
    "Elgato": ("1f1f1f", "0099ff"),
    "Shure": ("000000", "00aeef"),
    "Rode": ("c41e3a", "ffffff"),
    "Sony": ("000000", "ffffff"),
    "Apple": ("1d1d1f", "ffffff"),
    "DJI": ("000000", "0099ff"),
    "Insta360": ("ff6900", "ffffff"),
    "Aputure": ("0066cc", "ffffff"),
    "Anker": ("00b8d9", "ffffff"),
    "Govee": ("4a90e2", "ffffff"),
    "Wooting": ("ff6600", "ffffff"),
    "Razer": ("000000", "44d62c"),
    "Nanoleaf": ("1a1a2e", "00d9ff"),
}


def _img(brand: str, title: str, w: int = 800, h: int = 800) -> str:
    """Branded placeholder showing product name on the brand's colors.

    Override per-product via the admin once you've sourced real product
    photography — templates render whatever URL is in `image_url`.
    """
    bg, fg = BRAND_COLORS.get(brand, ("1a1a2e", "ffffff"))
    label = title.replace(brand, "").strip().replace(" ", "+") or brand.replace(" ", "+")
    return f"https://placehold.co/{w}x{h}/{bg}/{fg}?text={quote_plus(label)}&font=inter"


def _aliexpress(title: str) -> str:
    """AliExpress search URL with optional affiliate tracking parameter.

    Set ALIEXPRESS_AFFILIATE_TAG env var to your AliExpress Portals tracking
    ID and every affiliate link gets tagged for commission. Without a tag,
    the link still works — it just doesn't earn yet.
    """
    q = quote_plus(title)
    tag = os.environ.get("ALIEXPRESS_AFFILIATE_TAG", "").strip()
    base = f"https://www.aliexpress.com/wholesale?SearchText={q}"
    return f"{base}&aff_short_key={tag}" if tag else base


BRANDS = [
    {"name": "Grovemade", "domain": "grovemade.com", "category": "accessories"},
    {"name": "Keychron", "domain": "keychron.com", "category": "gadgets"},
    {"name": "Orbitkey", "domain": "orbitkey.com", "category": "accessories"},
    {"name": "BenQ", "domain": "benq.com", "category": "gadgets"},
    {"name": "Logitech", "domain": "logitech.com", "category": "gadgets"},
    {"name": "Elgato", "domain": "elgato.com", "category": "gadgets"},
    {"name": "Shure", "domain": "shure.com", "category": "gadgets"},
    {"name": "Rode", "domain": "rode.com", "category": "gadgets"},
    {"name": "Sony", "domain": "sony.com", "category": "gadgets"},
    {"name": "Apple", "domain": "apple.com", "category": "gadgets"},
    {"name": "DJI", "domain": "dji.com", "category": "gadgets"},
    {"name": "Insta360", "domain": "insta360.com", "category": "gadgets"},
    {"name": "Aputure", "domain": "aputure.com", "category": "gadgets"},
    {"name": "Anker", "domain": "anker.com", "category": "gadgets"},
    {"name": "Govee", "domain": "govee.com", "category": "home"},
    {"name": "Wooting", "domain": "wooting.io", "category": "gadgets"},
    {"name": "Razer", "domain": "razer.com", "category": "gadgets"},
    {"name": "Nanoleaf", "domain": "nanoleaf.me", "category": "home"},
]


PRODUCTS = [
    # ---------- Keyboards ----------
    {
        "brand": "Keychron",
        "title": "Keychron K2 HE Wireless Mechanical Keyboard",
        "price": Decimal("109.99"),
        "source_url": "https://www.keychron.com/products/keychron-k2-he-wireless-mechanical-keyboard",
        "main_claims": "Hall Effect magnetic switches with adjustable actuation\n75% compact layout perfect for creators\nBluetooth 5.1 + 2.4GHz + USB-C triple connectivity\nUp to 200 hours battery life",
        "specs": {"layout": "75% (84 keys)", "switches": "Gateron Double-Rail Magnetic", "connectivity": "Bluetooth 5.1 / 2.4GHz / USB-C", "battery": "4000mAh", "backlight": "South-facing RGB"},
        "variants": ["Carbon Black", "Shell White"],
    },
    {
        "brand": "Keychron",
        "title": "Keychron Q1 HE Wireless QMK Keyboard",
        "price": Decimal("219.99"),
        "source_url": "https://www.keychron.com/products/keychron-q1-he-wireless-qmk-custom-mechanical-keyboard",
        "main_claims": "Full aluminum CNC-machined body\nQMK/VIA programmable with magnetic switches\nGasket mount design for premium typing feel\nPerfect for content creators and developers",
        "specs": {"layout": "75% (82 keys)", "case": "6063 Aluminum CNC", "mount": "Gasket", "switches": "Gateron Double-Rail Magnetic", "weight": "3.95 lbs"},
        "variants": ["Carbon Black", "Shell White", "Navy Blue"],
    },
    {
        "brand": "Wooting",
        "title": "Wooting 80HE Analog Keyboard",
        "price": Decimal("199.00"),
        "source_url": "https://wooting.io/wooting-80he",
        "main_claims": "Lekker V2 magnetic switches with full analog input\nRapid Trigger and Snappy Tappy for esports edge\nTKL form factor with hot-swap support\nBest-in-class 8000 Hz polling rate",
        "specs": {"layout": "TKL (87 keys)", "switches": "Lekker V2 Magnetic", "polling": "8000 Hz", "features": "Rapid Trigger, Snappy Tappy, Mod Tap"},
        "variants": ["Black", "White"],
    },
    {
        "brand": "Razer",
        "title": "Razer Huntsman V3 Pro TKL",
        "price": Decimal("219.99"),
        "source_url": "https://www.razer.com/gaming-keyboards/razer-huntsman-v3-pro-tkl",
        "main_claims": "Razer Analog Optical Gen-2 switches\n8000 Hz polling for streamers and pro players\nDoubleshot PBT keycaps\nRapid Trigger for instant key resets",
        "specs": {"layout": "TKL", "switches": "Analog Optical Gen-2", "polling": "8000 Hz", "keycaps": "Doubleshot PBT"},
        "variants": ["Black"],
    },

    # ---------- Mice ----------
    {
        "brand": "Logitech",
        "title": "Logitech MX Master 4",
        "price": Decimal("119.99"),
        "source_url": "https://www.logitech.com/en-us/shop/p/mx-master-4-mouse",
        "main_claims": "Haptic feedback for precision actions\nMagSpeed electromagnetic scrolling\nWorks across 3 devices via Logi Bolt or Bluetooth\nUSB-C fast charge — full day in 60 seconds",
        "specs": {"sensor": "8000 DPI Darkfield", "buttons": "7 customizable", "battery": "Up to 70 days", "connectivity": "Bluetooth + Logi Bolt"},
        "variants": ["Graphite", "Pale Grey"],
    },
    {
        "brand": "Razer",
        "title": "Razer DeathAdder V4 Pro",
        "price": Decimal("169.99"),
        "source_url": "https://www.razer.com/gaming-mice/razer-deathadder-v4-pro",
        "main_claims": "Focus Pro 45K optical sensor\n56g lightweight ergonomic shell\nUp to 150 hour battery life\nGen-3 optical switches rated 100M clicks",
        "specs": {"sensor": "Focus Pro 45K", "weight": "56g", "polling": "8000 Hz HyperPolling", "battery": "150 hrs"},
        "variants": ["Black", "White"],
    },

    # ---------- Microphones ----------
    {
        "brand": "Shure",
        "title": "Shure SM7dB Dynamic Vocal Microphone",
        "price": Decimal("499.00"),
        "source_url": "https://www.shure.com/en-US/microphones/sm7db",
        "main_claims": "Built-in active preamp delivers +28 dB clean gain\nThe broadcast standard, now without an inline preamp\nFlat, wide-range frequency response for natural voice\nRugged construction designed for daily use",
        "specs": {"type": "Dynamic", "polar": "Cardioid", "preamp": "Built-in +28 dB", "connector": "XLR"},
        "variants": [],
    },
    {
        "brand": "Shure",
        "title": "Shure MV7+ Hybrid USB/XLR Microphone",
        "price": Decimal("279.00"),
        "source_url": "https://www.shure.com/en-US/microphones/mv7-plus",
        "main_claims": "USB-C and XLR — grow into pro studio without changing mic\nReal-time denoiser and auto level mode\nLED touch panel for mute and gain\nVoice Isolation Technology built in",
        "specs": {"type": "Dynamic", "polar": "Cardioid", "connectors": "USB-C + XLR", "features": "Denoiser, Auto Level, Touch panel"},
        "variants": ["Black", "White"],
    },
    {
        "brand": "Rode",
        "title": "Rode PodMic USB",
        "price": Decimal("199.00"),
        "source_url": "https://rode.com/en/microphones/usb/podmic-usb",
        "main_claims": "Hybrid USB-C and XLR connectivity\nClass-compliant — works with iPhone, iPad, USB-C Android\nAdvanced internal DSP and APHEX audio processing\nBuilt-in headphone output for zero-latency monitoring",
        "specs": {"type": "Dynamic broadcast", "polar": "Cardioid", "connectors": "USB-C + XLR", "dsp": "APHEX Aural Exciter, Big Bottom"},
        "variants": [],
    },
    {
        "brand": "Elgato",
        "title": "Elgato Wave DX Dynamic Microphone",
        "price": Decimal("139.99"),
        "source_url": "https://www.elgato.com/us/en/p/wave-dx",
        "main_claims": "XLR broadcast-style dynamic mic with rejection of room noise\nNo desk-thumps or keystrokes — tight cardioid pattern\nFlat 50 Hz–15 kHz response perfect for streaming\nDesigned to pair with Wave XLR interface",
        "specs": {"type": "Dynamic", "polar": "Cardioid", "frequency": "50 Hz - 15 kHz", "connector": "XLR"},
        "variants": [],
    },

    # ---------- Cameras / Webcams ----------
    {
        "brand": "Sony",
        "title": "Sony ZV-E10 II Vlog Camera",
        "price": Decimal("999.99"),
        "source_url": "https://electronics.sony.com/imaging/interchangeable-lens-cameras/all-interchangeable-lens-cameras/p/zvue10m2",
        "main_claims": "26MP APS-C sensor for crisp 4K 60p oversampled video\nProduct Showcase + AI face/eye AF for vloggers\n10-bit 4:2:2 internal recording\nFlip-out screen designed for selfie filming",
        "specs": {"sensor": "26MP APS-C Exmor R", "video": "4K 60p 10-bit 4:2:2", "stabilization": "Active mode IS", "weight": "377g"},
        "variants": ["Black", "White"],
    },
    {
        "brand": "DJI",
        "title": "DJI Pocket 3 Creator Combo",
        "price": Decimal("799.00"),
        "source_url": "https://www.dji.com/global/pocket-3",
        "main_claims": "1-inch CMOS sensor with 4K 120fps slow-mo\n3-axis mechanical gimbal — perfectly stable\n2-inch rotatable touchscreen for vertical and horizontal\nCreator Combo includes wireless mic and grip",
        "specs": {"sensor": "1-inch CMOS", "video": "4K 120fps", "gimbal": "3-axis mechanical", "screen": "2-inch rotatable"},
        "variants": ["Standard", "Creator Combo"],
    },
    {
        "brand": "Insta360",
        "title": "Insta360 GO 3S",
        "price": Decimal("449.99"),
        "source_url": "https://www.insta360.com/product/insta360-go-3s",
        "main_claims": "Tiny 39g action cam shoots 4K with FlowState stabilization\nMagnetic mounting — stick it anywhere\nAction Pod doubles as flip screen and remote\n170-min total battery with Action Pod",
        "specs": {"sensor": "1/2.3-inch", "video": "4K 30fps", "weight": "39g", "waterproof": "10m"},
        "variants": ["64GB", "128GB"],
    },
    {
        "brand": "Elgato",
        "title": "Elgato Facecam MK.2",
        "price": Decimal("149.99"),
        "source_url": "https://www.elgato.com/us/en/p/facecam-mk2",
        "main_claims": "Sony Starvis sensor for true 1080p60 streaming\nFixed-focus prime lens with no autofocus hunting\nUncompressed video output via USB-C\nCamera Hub app — full DSLR-level control",
        "specs": {"sensor": "Sony Starvis CMOS", "resolution": "1080p60", "lens": "Elgato Prime f/2.4", "fov": "84°"},
        "variants": [],
    },
    {
        "brand": "Logitech",
        "title": "Logitech MX Brio 4K Webcam",
        "price": Decimal("199.99"),
        "source_url": "https://www.logitech.com/en-us/shop/p/mx-brio",
        "main_claims": "True 4K with 8.5MP Sony sensor\nAI-driven Show Mode for downward demos\nPrivacy shutter built into the bezel\nWorks with Logi Options+ for fine-tuning",
        "specs": {"resolution": "4K 30fps / 1080p 60fps", "sensor": "8.5MP Sony", "fov": "90°", "mount": "Magnetic"},
        "variants": ["Graphite", "Pale Grey"],
    },

    # ---------- Streaming gear ----------
    {
        "brand": "Elgato",
        "title": "Elgato Stream Deck MK.2",
        "price": Decimal("149.99"),
        "source_url": "https://www.elgato.com/us/en/p/stream-deck-mk2",
        "main_claims": "15 customizable LCD keys — one-tap any action\nDeep integration with OBS, Streamlabs, Twitch, Discord\nProfile-switching for different apps\nReplaceable faceplates for setup aesthetics",
        "specs": {"keys": "15 LCD", "interface": "USB-C", "profiles": "Unlimited", "size": "118 x 84 x 21 mm"},
        "variants": ["Black", "White"],
    },
    {
        "brand": "Elgato",
        "title": "Elgato Key Light Air",
        "price": Decimal("129.99"),
        "source_url": "https://www.elgato.com/us/en/p/key-light-air",
        "main_claims": "1400 lumens of soft, even light\nTunable from 2900K to 7000K color temperature\nWi-Fi controlled — no remote, no batteries\nSlim profile mounts on desk or wall",
        "specs": {"lumens": 1400, "color_temp": "2900K-7000K", "control": "Wi-Fi", "mount": "Desk clamp"},
        "variants": [],
    },
    {
        "brand": "Aputure",
        "title": "Aputure MC Pro RGBWW Mini Light",
        "price": Decimal("149.00"),
        "source_url": "https://www.aputure.com/products/mc-pro",
        "main_claims": "Pocket-size RGBWW LED packs full creative control\nBuilt-in magnets for any setup\nSidus Link app for full color and effects\nUSB-C PD charging plus removable battery",
        "specs": {"output": "1500 lux @ 1m", "cri": "CRI/TLCI 96+", "color": "RGBWW full gamut", "mount": "Magnetic + 1/4-20"},
        "variants": [],
    },
    {
        "brand": "BenQ",
        "title": "BenQ ScreenBar Halo Monitor Light",
        "price": Decimal("179.00"),
        "source_url": "https://www.benq.com/en-us/lighting/monitor-light/screenbar-halo.html",
        "main_claims": "Asymmetric light that illuminates desk without screen glare\nWireless controller with ambient light sensor\nBack-light for immersive glow effect\nAuto-dimming adapts to environment",
        "specs": {"power": "USB-powered (5V 1A)", "color_temp": "2700K-6500K", "luminance": "500 lux at 45cm", "controller": "Wireless dial with ambient sensor"},
        "variants": [],
    },
    {
        "brand": "BenQ",
        "title": "BenQ ScreenBar Pro Monitor Light",
        "price": Decimal("149.00"),
        "source_url": "https://www.benq.com/en-us/lighting/monitor-light/screenbar-pro.html",
        "main_claims": "Built-in proximity sensor auto on/off\n16 preset lighting modes\nNo desk space required - clips onto monitor\nFlicker-free and blue light safe",
        "specs": {"power": "USB-powered (5V 1.3A)", "color_temp": "2700K-6500K", "luminance": "530 lux at 45cm", "features": "Proximity sensor, 16 presets"},
        "variants": [],
    },

    # ---------- Headphones / audio ----------
    {
        "brand": "Sony",
        "title": "Sony WH-1000XM6 Wireless Headphones",
        "price": Decimal("449.00"),
        "source_url": "https://electronics.sony.com/audio/headphones/headband/p/wh1000xm6",
        "main_claims": "Industry-leading noise cancellation with QN3 processor\n30-hour battery with quick charge — 3 min for 3 hours\nLDAC + Hi-Res Audio Wireless support\nCrystal-clear voice pickup for calls",
        "specs": {"battery": "30 hours ANC on", "drivers": "30mm", "codecs": "LDAC, AAC, SBC", "weight": "254g"},
        "variants": ["Black", "Silver", "Midnight Blue"],
    },
    {
        "brand": "Apple",
        "title": "Apple AirPods Max (USB-C)",
        "price": Decimal("549.00"),
        "source_url": "https://www.apple.com/shop/buy-airpods/airpods-max",
        "main_claims": "Adaptive Audio blends ANC and Transparency\nPersonalized Spatial Audio with dynamic head tracking\nUSB-C with lossless 24-bit/48kHz audio for Vision Pro\nMachined aluminum cups, mesh canopy",
        "specs": {"battery": "20 hours ANC", "connectivity": "USB-C, Bluetooth 5.0", "drivers": "40mm dynamic", "weight": "385g"},
        "variants": ["Midnight", "Starlight", "Blue", "Purple", "Orange"],
    },

    # ---------- Desk accessories ----------
    {
        "brand": "Grovemade",
        "title": "Grovemade Wood Desk Shelf",
        "price": Decimal("220.00"),
        "source_url": "https://grovemade.com/product/wood-desk-shelf/",
        "main_claims": "Handcrafted solid hardwood desk shelf\nElevates monitor to ergonomic height\nCable management channel built in\nSustainably sourced American hardwood",
        "specs": {"material": "Walnut / Maple hardwood", "dimensions": "32 x 10.5 x 4 inches", "weight": "6.5 lbs", "finish": "Natural oil"},
        "variants": ["Walnut", "Maple"],
    },
    {
        "brand": "Grovemade",
        "title": "Grovemade Leather Desk Pad",
        "price": Decimal("120.00"),
        "source_url": "https://grovemade.com/product/matte-desk-pad/",
        "main_claims": "Premium vegetable-tanned leather\nLarge work surface 27.5 x 17.5 inches\nDevelops rich patina over time\nNon-slip cork base",
        "specs": {"material": "Vegetable-tanned leather + cork base", "dimensions": "27.5 x 17.5 x 0.2 inches"},
        "variants": ["Small", "Large", "Extra Large"],
    },
    {
        "brand": "Orbitkey",
        "title": "Orbitkey Desk Mat",
        "price": Decimal("64.90"),
        "source_url": "https://www.orbitkey.com/collections/desk-mat/products/desk-mat",
        "main_claims": "Vegan leather desk mat with magnetic cable holder\nDocument hideaway pocket underneath\nEasy-clean stain-resistant surface\nMinimalist design fits any setup",
        "specs": {"material": "Vegan leather + recycled PET felt base", "dimensions": "Medium: 68 x 32cm, Large: 84 x 36cm"},
        "variants": ["Stone Grey", "Black", "Navy"],
    },

    # ---------- Charging / accessories ----------
    {
        "brand": "Anker",
        "title": "Anker Prime 100W GaN Charger (3-Port)",
        "price": Decimal("79.99"),
        "source_url": "https://www.anker.com/products/a2343",
        "main_claims": "100W total output across 3 ports\nGaN II tech keeps it pocket-sized\nCharges MacBook Pro 16, iPhone, AirPods together\nIntelligent power distribution per device",
        "specs": {"output": "100W total", "ports": "2x USB-C, 1x USB-A", "size": "65 x 45 x 31 mm", "tech": "GaN II"},
        "variants": ["Black"],
    },

    # ---------- Smart lighting ----------
    {
        "brand": "Govee",
        "title": "Govee Glide RGBIC Wall Light",
        "price": Decimal("149.99"),
        "source_url": "https://us.govee.com/products/govee-glide-wall-light",
        "main_claims": "Modular hexagonal panels — design any wall pattern\nRGBIC tech displays multiple colors at once\nAI music sync reacts to your stream\n64 scene presets and unlimited DIY",
        "specs": {"panels": "Hexagonal modular", "tech": "RGBIC", "control": "Wi-Fi + Govee Home app", "compat": "Alexa, Google Assistant"},
        "variants": ["Hexa 10-pack", "Hexa Ultra 7-pack"],
    },
    {
        "brand": "Nanoleaf",
        "title": "Nanoleaf Shapes Hexagons Smarter Kit",
        "price": Decimal("199.99"),
        "source_url": "https://nanoleaf.me/en-US/products/nanoleaf-shapes/hexagons-smarter-kit",
        "main_claims": "9 modular touch-reactive hexagon panels\nTrue HomeKit Adaptive Lighting support\n16M+ colors, hundreds of community scenes\nMusic and screen-mirror sync",
        "specs": {"panels": "9 hexagons", "control": "Touch + app + voice", "compat": "HomeKit, Alexa, Google, Matter"},
        "variants": [],
    },
]


TRENDS = [
    {
        "product": "Sony ZV-E10 II Vlog Camera",
        "why_trending": "The vertical-video creator boom of 2026 made the ZV-E10 II the default upgrade pick for TikTok and YouTube Shorts creators leaving their phone behind. The articulating screen, in-camera Product Showcase, and oversampled 4K make it the camera every full-time creator owns this year.",
        "creator_hooks": ["Phone-to-camera upgrade content", "Vertical 4K shooting tips", "Creator setup tour staple"],
        "platform_fit": ["youtube", "tiktok", "instagram"],
        "trend_score": 10,
    },
    {
        "product": "Shure MV7+ Hybrid USB/XLR Microphone",
        "why_trending": "Podcast-style YouTube boomed in 2026 — every commentary creator is upgrading from the Blue Yeti era to a real broadcast dynamic. The MV7+ leads because it grows with creators: USB-C today, XLR studio tomorrow, no replacement needed.",
        "creator_hooks": ["Mic upgrade from Yeti", "Podcast-style YouTube build", "Voice-over quality test"],
        "platform_fit": ["youtube", "tiktok", "podcast"],
        "trend_score": 9,
    },
    {
        "product": "DJI Pocket 3 Creator Combo",
        "why_trending": "The Pocket 3 is the most-recommended camera for travel vloggers in 2026. The flip-up screen and 1-inch sensor changed the game, and it now ships with the wireless mic that actually replaces lavalier kits.",
        "creator_hooks": ["Travel vlog setup", "One-take street content", "Run-and-gun B-roll"],
        "platform_fit": ["youtube", "tiktok", "instagram"],
        "trend_score": 10,
    },
    {
        "product": "Wooting 80HE Analog Keyboard",
        "why_trending": "Hall Effect keyboards graduated from gaming-only to full creator territory in 2026. Wooting's Rapid Trigger and Snappy Tappy features made it the top recommendation for streamers playing FPS games on camera.",
        "creator_hooks": ["FPS streamer gear", "HE switch demos", "Gaming chair tour upgrade"],
        "platform_fit": ["youtube", "tiktok", "twitch"],
        "trend_score": 9,
    },
    {
        "product": "Keychron K2 HE Wireless Mechanical Keyboard",
        "why_trending": "The most affordable Hall Effect keyboard in 2026 that still ticks every creator box. Adjustable actuation per key means one keyboard for typing scripts and gaming reels.",
        "creator_hooks": ["Adjustable actuation for different tasks", "Clean aesthetic for desk setups", "Triple connectivity for multi-device workflows"],
        "platform_fit": ["youtube", "tiktok", "instagram"],
        "trend_score": 8,
    },
    {
        "product": "Elgato Stream Deck MK.2",
        "why_trending": "Stream Deck became the universal creator control panel in 2026. Now used as much by short-form editors and podcasters as live streamers — one tap to switch scenes, mute, export, post.",
        "creator_hooks": ["Editing workflow tour", "Hidden Stream Deck use cases", "Productivity hack for creators"],
        "platform_fit": ["youtube", "tiktok", "twitch"],
        "trend_score": 9,
    },
    {
        "product": "BenQ ScreenBar Halo Monitor Light",
        "why_trending": "The Halo's back-glow is the single most copied detail in 2026 desk-tour videos. Every aesthetic setup has it, and the wireless controller is now a must-have for clean-cable creator setups.",
        "creator_hooks": ["Perfect for desk setup videos", "Back-glow creates viral aesthetics", "Practical upgrade every creator needs"],
        "platform_fit": ["youtube", "tiktok", "instagram"],
        "trend_score": 8,
    },
    {
        "product": "Logitech MX Master 4",
        "why_trending": "The new haptic feedback engine made the MX Master 4 the most-recommended productivity mouse for creators in 2026. Editors swear by the per-app gesture buttons.",
        "creator_hooks": ["Editor workflow hack", "Productivity gear upgrade", "Cross-device pointer tour"],
        "platform_fit": ["youtube", "instagram"],
        "trend_score": 8,
    },
    {
        "product": "Insta360 GO 3S",
        "why_trending": "Hands-free POV is the dominant short-form format of 2026, and the GO 3S is what every TikTok cooking, lifestyle, and adventure creator straps to themselves.",
        "creator_hooks": ["POV cooking content", "Wearable cam setup", "Creative mounting hacks"],
        "platform_fit": ["tiktok", "instagram", "youtube"],
        "trend_score": 9,
    },
    {
        "product": "Govee Glide RGBIC Wall Light",
        "why_trending": "The hex-panel aesthetic dominated 2026 desk and gaming setup tours. Govee's price point made it the entry-level pick over Nanoleaf for new streamers.",
        "creator_hooks": ["Wall art for streamers", "RGB setup glow-up", "Music-reactive ambient"],
        "platform_fit": ["youtube", "tiktok", "twitch"],
        "trend_score": 7,
    },
    {
        "product": "Sony WH-1000XM6 Wireless Headphones",
        "why_trending": "The XM6 is the editing headphone of choice in 2026 — strong mids that translate well to laptop and phone playback, ANC that blocks out coworking spaces.",
        "creator_hooks": ["Editor monitoring on-the-go", "Travel creator essentials", "Voice-over scratch track"],
        "platform_fit": ["youtube", "tiktok"],
        "trend_score": 7,
    },
    {
        "product": "Grovemade Wood Desk Shelf",
        "why_trending": "Quiet luxury swept creator interiors in 2026. Hardwood and matte finishes became the visual language of the most-watched setup tours.",
        "creator_hooks": ["Premium look for setup content", "Practical cable management", "Pairs with any desk setup theme"],
        "platform_fit": ["youtube", "instagram"],
        "trend_score": 7,
    },
]


COMPARISONS = [
    {
        "title": "Keychron K2 HE vs Wooting 80HE: Best Hall Effect Keyboard 2026",
        "product_a": "Keychron K2 HE Wireless Mechanical Keyboard",
        "product_b": "Wooting 80HE Analog Keyboard",
        "pros_a": "Wireless triple-connectivity (BT, 2.4G, USB-C)\n200-hour battery for travel creators\nMore affordable at $109.99\nGreat all-rounder for typing and gaming",
        "cons_a": "Plastic build vs aluminum\nNo Rapid Trigger software polish of Wooting\nNot fully analog input mappable",
        "pros_b": "True analog input mapping for racing/flight sims\nIndustry-leading Rapid Trigger and Snappy Tappy\n8000 Hz polling for esports edge\nWootility software is best-in-class",
        "cons_b": "Wired only — no Bluetooth\nNearly 2x the price at $199\nLouder switches less suited to recording voice",
        "winner_for": "Pick the K2 HE if you're a creator who types and games casually and needs wireless. Pick the Wooting 80HE if you stream FPS games or compete — the analog control is unmatched.",
    },
    {
        "title": "Shure SM7dB vs MV7+: Which Broadcast Mic in 2026?",
        "product_a": "Shure SM7dB Dynamic Vocal Microphone",
        "product_b": "Shure MV7+ Hybrid USB/XLR Microphone",
        "pros_a": "True broadcast standard heard on Spotify's biggest podcasts\nBuilt-in preamp eliminates Cloudlifter for $400+ less in extras\nFlat frequency response — pure, natural voice\nBomb-proof build, lasts decades",
        "cons_a": "XLR only — needs an interface ($200+ extra)\nMust have proper audio chain knowledge\n$220 more than MV7+",
        "pros_b": "USB-C and XLR — start simple, upgrade later\nReal-time denoiser kills room reverb\nTouch panel for mute and gain\nAuto Level mode = consistent loudness",
        "cons_b": "DSP can sound 'processed' if pushed\nLess pristine than SM7dB on a real interface\nUSB-C cable proprietary",
        "winner_for": "SM7dB is the right answer if you already have an interface and want the absolute best voice. MV7+ wins if you're starting now or work cross-platform — it's the most flexible mic for 2026 creators.",
    },
    {
        "title": "DJI Pocket 3 vs Sony ZV-E10 II: Best 2026 Vlog Camera?",
        "product_a": "DJI Pocket 3 Creator Combo",
        "product_b": "Sony ZV-E10 II Vlog Camera",
        "pros_a": "Stabilized one-handed shooting — no shake\nFlip-screen for vertical and horizontal\nMechanical gimbal beats any IS\nReady to roll out of the bag, no lens swapping",
        "cons_a": "Fixed lens — no creative options\n1-inch sensor maxes out in low light\nNot a full hybrid stills camera",
        "pros_b": "26MP APS-C sensor — better low light, depth of field\nInterchangeable lenses for any look\n4K 60p 10-bit 4:2:2 internal recording\nGrows with you into pro work",
        "cons_b": "Bigger and heavier — not pocketable\nNo internal stabilization beats Pocket gimbal\nLearning curve for menus and lens choice",
        "winner_for": "Pocket 3 wins for travel creators, daily vloggers, and anyone who wants 'pull it out and shoot.' ZV-E10 II is the pick if you want one camera for vlogs, B-roll, and pro client work.",
    },
    {
        "title": "BenQ ScreenBar Halo vs Pro: Which Monitor Light Should Creators Buy?",
        "product_a": "BenQ ScreenBar Halo Monitor Light",
        "product_b": "BenQ ScreenBar Pro Monitor Light",
        "pros_a": "Wireless dial controller feels premium\nBack-light illumination for ambient effects\nAmbient light sensor auto-adjusts\nPerfect for content creation backdrops",
        "cons_a": "$30 more expensive than Pro\nController needs AAA batteries\nSlightly lower max luminance",
        "pros_b": "Built-in proximity sensor (auto on/off)\n16 preset lighting modes\nHigher max luminance at 530 lux\nMore affordable at $149",
        "cons_b": "No wireless controller\nNo back-light ambient effect\nTouch controls on the bar itself",
        "winner_for": "Halo for creators chasing the ambient back-glow that's everywhere in 2026 setup tours. Pro for pure productivity — its proximity auto on/off is a quiet but daily-life upgrade.",
    },
    {
        "title": "Sony WH-1000XM6 vs AirPods Max USB-C: Editor's Pick 2026",
        "product_a": "Sony WH-1000XM6 Wireless Headphones",
        "product_b": "Apple AirPods Max (USB-C)",
        "pros_a": "Best ANC on the market for travel/coworking\nLDAC support for hi-res audio\n30-hour battery with quick charge\n$100 cheaper than AirPods Max",
        "cons_a": "Plastic build feels less premium\nAndroid/iOS feature parity uneven\nFolds, but case is bulky",
        "pros_b": "Lossless 24-bit/48kHz over USB-C\nMachined aluminum + Spatial Audio\nSeamless Apple ecosystem switching\nBest-in-class for Vision Pro audio",
        "cons_b": "$549 — most expensive in class\nOnly 20-hour battery\n385g — heaviest in this segment",
        "winner_for": "XM6 is the practical creator pick — better travel battery, better isolation, lower price. AirPods Max wins only if you're deep in Apple Vision Pro and want lossless wired editing.",
    },
]


USECASES = [
    {
        "title": "Best Creator Starter Kit Under $500 (2026)",
        "audience": "First-time creators going from phone to real gear",
        "budget_max": 500,
        "top_pick_titles": [
            "Shure MV7+ Hybrid USB/XLR Microphone",
            "Logitech MX Brio 4K Webcam",
            "Elgato Key Light Air",
            "Keychron K2 HE Wireless Mechanical Keyboard",
        ],
        "cautions": "Skip ring lights and ringless soft boxes — they create the 'cheap creator look' viewers can spot instantly. Spend on a real key light first, even if you have to wait on the camera upgrade.",
    },
    {
        "title": "YouTube Tech Review Studio Setup Under $2500",
        "audience": "Tech reviewers building a recognizable on-camera studio",
        "budget_max": 2500,
        "top_pick_titles": [
            "Sony ZV-E10 II Vlog Camera",
            "Shure SM7dB Dynamic Vocal Microphone",
            "Aputure MC Pro RGBWW Mini Light",
            "BenQ ScreenBar Halo Monitor Light",
            "Grovemade Wood Desk Shelf",
        ],
        "cautions": "Lens cost is hidden in the camera body price. Budget at least $400 extra for one prime + one zoom. And don't forget the audio interface for the SM7dB.",
    },
    {
        "title": "Best TikTok / Short-Form Vlogger Setup 2026",
        "audience": "Short-form creators shooting daily on the move",
        "budget_max": 1500,
        "top_pick_titles": [
            "DJI Pocket 3 Creator Combo",
            "Insta360 GO 3S",
            "Anker Prime 100W GaN Charger (3-Port)",
            "Sony WH-1000XM6 Wireless Headphones",
        ],
        "cautions": "Resist the urge to bring a full mirrorless on the road — short-form lives or dies on consistency, and pocketable gear means you actually shoot every day.",
    },
    {
        "title": "Live Streamer Setup Under $1200 (2026)",
        "audience": "Twitch and Kick streamers building their first pro rig",
        "budget_max": 1200,
        "top_pick_titles": [
            "Elgato Stream Deck MK.2",
            "Elgato Wave DX Dynamic Microphone",
            "Elgato Facecam MK.2",
            "Wooting 80HE Analog Keyboard",
            "Govee Glide RGBIC Wall Light",
        ],
        "cautions": "Don't buy the full Elgato ecosystem on day one. Start with mic + Stream Deck, see what your stream actually needs in month two, then expand.",
    },
    {
        "title": "Podcaster Solo Setup Under $1000 (2026)",
        "audience": "Solo podcasters who plan to publish video on YouTube too",
        "budget_max": 1000,
        "top_pick_titles": [
            "Shure MV7+ Hybrid USB/XLR Microphone",
            "Logitech MX Brio 4K Webcam",
            "Sony WH-1000XM6 Wireless Headphones",
            "Grovemade Leather Desk Pad",
        ],
        "cautions": "If you ever plan to add a guest, buy two of the same mic from day one — mismatched mic sounds are obvious to listeners and impossible to fully fix in post.",
    },
    {
        "title": "Aesthetic Desk Setup for Creators ($800)",
        "audience": "Creators chasing the quiet-luxury / cozy desk-tour look",
        "budget_max": 800,
        "top_pick_titles": [
            "Grovemade Wood Desk Shelf",
            "Grovemade Leather Desk Pad",
            "Orbitkey Desk Mat",
            "BenQ ScreenBar Halo Monitor Light",
            "Logitech MX Master 4",
        ],
        "cautions": "Wood and leather develop patina, RGB doesn't. If you want a desk that ages well on camera year over year, lean into natural materials and skip the lighting overload.",
    },
]


class Command(BaseCommand):
    help = "Populate database with realistic 2026 creator gear data"

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
                    "logo_url": b.get("logo_url", ""),
                },
            )
            brands[b["name"]] = obj
            self.stdout.write(f"  Brand: {obj.name} ({'created' if created else 'exists'})")

        # Products — update_or_create so re-runs refresh image URLs/prices
        products = {}
        for p in PRODUCTS:
            brand = brands[p["brand"]]
            obj, created = Product.objects.update_or_create(
                slug=slugify(p["title"])[:255],
                defaults={
                    "title": p["title"],
                    "brand": brand,
                    "price": p["price"],
                    "currency": "USD",
                    # source_url -> Amazon search so the link always resolves
                    # to a real listing with current price/availability
                    "source_url": _aliexpress(f"{p['brand']} {p['title']}"),
                    "image_url": p.get("image_url") or _img(p["brand"], p["title"]),
                    "main_claims": p["main_claims"],
                    "specs": p["specs"],
                    "variants": p["variants"],
                    "last_crawled": timezone.now(),
                    "is_active": True,
                },
            )
            products[p["title"]] = obj
            self.stdout.write(f"  Product: {obj.title} ({'created' if created else 'updated'})")

        # Trend entries
        for t in TRENDS:
            if t["product"] not in products:
                continue
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
            if c["product_a"] not in products or c["product_b"] not in products:
                continue
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

        # Affiliate links — refresh URL on every run so AMAZON_AFFILIATE_TAG
        # changes propagate. AffiliateRedirectView prefers AffiliateLink over
        # source_url, so updating here is what actually changes outbound clicks.
        for product in products.values():
            amazon_url = _aliexpress(f"{product.brand.name} {product.title}")
            _, created = AffiliateLink.objects.update_or_create(
                product=product,
                defaults={
                    "network_name": "AliExpress",
                    "affiliate_url": amazon_url,
                },
            )
            self.stdout.write(
                f"  AffiliateLink: {product.title} ({'created' if created else 'updated'})"
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seed data populated successfully!"))
        self.stdout.write(f"  Brands: {Brand.objects.count()}")
        self.stdout.write(f"  Products: {Product.objects.count()}")
        self.stdout.write(f"  Trends: {TrendEntry.objects.count()}")
        self.stdout.write(f"  Comparisons: {Comparison.objects.count()}")
        self.stdout.write(f"  Use Cases: {UseCasePage.objects.count()}")
        self.stdout.write(f"  Affiliate Links: {AffiliateLink.objects.count()}")
