from datetime import timedelta

from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

from .models import (
    AffiliateLink,
    Brand,
    ClickLog,
    Comparison,
    EmailSubscriber,
    Product,
    ProductChangeLog,
    RawCrawl,
    TrendEntry,
    UseCasePage,
)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "domain", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "brand", "price", "is_active", "last_crawled")
    list_filter = ("is_active", "brand")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "brand", "price", "currency", "image_url", "source_url", "main_claims", "specs", "variants", "last_crawled", "is_active")}),
        ("SEO", {"fields": ("meta_title", "meta_description", "og_image"), "classes": ("collapse",)}),
    )


@admin.register(TrendEntry)
class TrendEntryAdmin(admin.ModelAdmin):
    list_display = ("product", "trend_score", "added_at")
    list_filter = ("trend_score",)


@admin.register(Comparison)
class ComparisonAdmin(admin.ModelAdmin):
    list_display = ("title", "product_a", "product_b", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "product_a", "product_b", "pros_a", "cons_a", "pros_b", "cons_b", "winner_for")}),
        ("SEO", {"fields": ("meta_title", "meta_description", "og_image"), "classes": ("collapse",)}),
    )


@admin.register(UseCasePage)
class UseCasePageAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "budget_max", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "audience", "budget_max", "top_picks", "cautions")}),
        ("SEO", {"fields": ("meta_title", "meta_description", "og_image"), "classes": ("collapse",)}),
    )


@admin.register(RawCrawl)
class RawCrawlAdmin(admin.ModelAdmin):
    list_display = ("brand_domain", "url", "crawled_at")
    list_filter = ("brand_domain",)
    readonly_fields = ("response",)


@admin.register(ProductChangeLog)
class ProductChangeLogAdmin(admin.ModelAdmin):
    list_display = ("product", "field_name", "detected_at")
    list_filter = ("field_name", "detected_at")
    readonly_fields = ("product", "field_name", "old_value", "new_value", "detected_at")


# ---------------------------------------------------------------------------
# Affiliate & Subscriber admin
# ---------------------------------------------------------------------------
class ClickLogInline(admin.TabularInline):
    model = ClickLog
    readonly_fields = ("referrer", "clicked_at")
    extra = 0


@admin.register(AffiliateLink)
class AffiliateLinkAdmin(admin.ModelAdmin):
    list_display = ("product", "network_name", "click_count", "created_at")
    list_filter = ("network_name",)
    inlines = [ClickLogInline]


@admin.register(ClickLog)
class ClickLogAdmin(admin.ModelAdmin):
    list_display = ("affiliate_link", "referrer", "clicked_at")
    list_filter = ("clicked_at",)
    readonly_fields = ("affiliate_link", "referrer", "clicked_at")


@admin.register(EmailSubscriber)
class EmailSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "source_page", "subscribed_at", "is_active")
    list_filter = ("is_active", "subscribed_at")
    search_fields = ("email",)


# ---------------------------------------------------------------------------
# Revenue dashboard at /admin/revenue/
# ---------------------------------------------------------------------------
def revenue_dashboard_view(request):
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    clicks_this_week = ClickLog.objects.filter(clicked_at__gte=week_ago).count()
    clicks_this_month = ClickLog.objects.filter(clicked_at__gte=month_ago).count()

    top_products = (
        AffiliateLink.objects
        .select_related("product")
        .order_by("-click_count")[:5]
    )

    subscriber_total = EmailSubscriber.objects.filter(is_active=True).count()
    subscribers_last_30 = EmailSubscriber.objects.filter(
        subscribed_at__gte=month_ago, is_active=True
    ).count()

    context = {
        **admin.site.each_context(request),
        "title": "Revenue Dashboard",
        "clicks_this_week": clicks_this_week,
        "clicks_this_month": clicks_this_month,
        "top_products": top_products,
        "subscriber_total": subscriber_total,
        "subscribers_last_30": subscribers_last_30,
    }
    return TemplateResponse(request, "admin/revenue_dashboard.html", context)


# Inject the revenue URL into the default admin site
_original_get_urls = admin.site.get_urls.__func__


def _patched_get_urls(self):
    custom = [
        path("revenue/", self.admin_view(revenue_dashboard_view), name="revenue-dashboard"),
    ]
    return custom + _original_get_urls(self)


admin.site.get_urls = _patched_get_urls.__get__(admin.site)
