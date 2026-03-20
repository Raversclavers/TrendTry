from django.db import models
from django.urls import reverse


class Brand(models.Model):
    class Category(models.TextChoices):
        GADGETS = "gadgets", "Gadgets"
        ACCESSORIES = "accessories", "Accessories"
        GROOMING = "grooming", "Grooming"
        FASHION = "fashion", "Fashion"
        HOME = "home", "Home"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    domain = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    logo_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:brand-detail", kwargs={"slug": self.slug})


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="products"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    image_url = models.URLField(blank=True)
    source_url = models.URLField(blank=True)
    main_claims = models.TextField(blank=True)
    specs = models.JSONField(default=dict, blank=True)
    variants = models.JSONField(default=list, blank=True)
    last_crawled = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    og_image = models.URLField(blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("catalog:product-detail", kwargs={"slug": self.slug})


class TrendEntry(models.Model):
    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="trend_entry"
    )
    why_trending = models.TextField()
    creator_hooks = models.JSONField(
        default=list, blank=True, help_text="List of string angles for creators"
    )
    platform_fit = models.JSONField(
        default=list,
        blank=True,
        help_text='Platforms this product fits, e.g. ["tiktok","youtube"]',
    )
    trend_score = models.IntegerField(
        help_text="1-10 score indicating trend strength"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-trend_score", "-added_at"]
        verbose_name_plural = "trend entries"

    def __str__(self):
        return f"Trend: {self.product.title} ({self.trend_score}/10)"

    def get_absolute_url(self):
        return reverse(
            "catalog:product-detail", kwargs={"slug": self.product.slug}
        )


class Comparison(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    product_a = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="comparisons_as_a"
    )
    product_b = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="comparisons_as_b"
    )
    pros_a = models.TextField(blank=True)
    cons_a = models.TextField(blank=True)
    pros_b = models.TextField(blank=True)
    cons_b = models.TextField(blank=True)
    winner_for = models.TextField(
        blank=True, help_text="Description of who each product is best for"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    og_image = models.URLField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("catalog:comparison-detail", kwargs={"slug": self.slug})


class UseCasePage(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    audience = models.CharField(max_length=255)
    budget_max = models.IntegerField(help_text="Maximum budget in USD")
    top_picks = models.ManyToManyField(Product, related_name="use_case_pages", blank=True)
    cautions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    og_image = models.URLField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("catalog:usecase-detail", kwargs={"slug": self.slug})


class ProductChangeLog(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="change_logs"
    )
    field_name = models.CharField(max_length=60)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return f"{self.product} — {self.field_name} @ {self.detected_at:%Y-%m-%d %H:%M}"


class AffiliateLink(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="affiliate_links"
    )
    network_name = models.CharField(
        max_length=120, help_text='e.g. "Amazon Associates", "ShareASale"'
    )
    affiliate_url = models.URLField()
    click_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.title} — {self.network_name}"


class ClickLog(models.Model):
    affiliate_link = models.ForeignKey(
        AffiliateLink, on_delete=models.CASCADE, related_name="click_logs"
    )
    referrer = models.URLField(blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-clicked_at"]

    def __str__(self):
        return f"Click on {self.affiliate_link} @ {self.clicked_at:%Y-%m-%d %H:%M}"


class EmailSubscriber(models.Model):
    email = models.EmailField(unique=True)
    source_page = models.CharField(max_length=255, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self):
        return self.email


class RawCrawl(models.Model):
    brand_domain = models.CharField(max_length=255)
    url = models.URLField()
    response = models.JSONField()
    crawled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-crawled_at"]

    def __str__(self):
        return f"{self.brand_domain} — {self.crawled_at:%Y-%m-%d %H:%M}"
