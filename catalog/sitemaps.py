from django.contrib.sitemaps import Sitemap

from .models import Comparison, Product, UseCasePage


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.last_crawled


class ComparisonSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Comparison.objects.all()

    def lastmod(self, obj):
        return obj.created_at


class UseCasePageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return UseCasePage.objects.all()

    def lastmod(self, obj):
        return obj.created_at
