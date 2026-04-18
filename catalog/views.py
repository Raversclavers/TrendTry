from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from meta.views import Meta

from .models import (
    AffiliateLink,
    Brand,
    ClickLog,
    Comparison,
    EmailSubscriber,
    Product,
    TrendEntry,
    UseCasePage,
)


def _build_meta(obj, **overrides):
    """Build a Meta object from a model instance with SEO fields."""
    return Meta(
        title=obj.meta_title or obj.title,
        description=obj.meta_description or "",
        image=overrides.get("image", getattr(obj, "og_image", "") or getattr(obj, "image_url", "")),
        url=obj.get_absolute_url(),
    )


class HomeView(TemplateView):
    template_name = "catalog/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trends"] = (
            TrendEntry.objects
            .select_related("product__brand")
            .filter(product__is_active=True)[:6]
        )
        ctx["comparisons"] = (
            Comparison.objects
            .select_related("product_a__brand", "product_b__brand")
            .filter(product_a__is_active=True, product_b__is_active=True)[:3]
        )
        return ctx


class TrendingListView(ListView):
    model = TrendEntry
    template_name = "catalog/trending_list.html"
    context_object_name = "trends"
    paginate_by = 12

    def get_queryset(self):
        return (
            TrendEntry.objects
            .select_related("product__brand")
            .order_by("-trend_score", "-added_at")
        )


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.select_related("brand")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object
        try:
            ctx["trend_entry"] = product.trend_entry
        except TrendEntry.DoesNotExist:
            ctx["trend_entry"] = None
        ctx["comparisons"] = (
            Comparison.objects
            .filter(Q(product_a=product) | Q(product_b=product))
            .select_related("product_a", "product_b")
        )
        ctx["meta"] = _build_meta(product, image=product.og_image or product.image_url)
        return ctx


class BrandDetailView(DetailView):
    model = Brand
    template_name = "catalog/brand_detail.html"
    context_object_name = "brand"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["products"] = (
            self.object.products
            .filter(is_active=True)
            .order_by("-id")
        )
        return ctx


class ComparisonDetailView(DetailView):
    model = Comparison
    template_name = "catalog/comparison_detail.html"
    context_object_name = "comparison"

    def get_queryset(self):
        return Comparison.objects.select_related(
            "product_a__brand", "product_b__brand"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["meta"] = _build_meta(self.object)
        return ctx


class ComparisonListView(ListView):
    model = Comparison
    template_name = "catalog/comparison_list.html"
    context_object_name = "comparisons"
    paginate_by = 12

    def get_queryset(self):
        return Comparison.objects.select_related("product_a__brand", "product_b__brand")


class BrandListView(ListView):
    model = Brand
    template_name = "catalog/brand_list.html"
    context_object_name = "brands"

    def get_queryset(self):
        return Brand.objects.all()


class UseCaseListView(ListView):
    model = UseCasePage
    template_name = "catalog/usecase_list.html"
    context_object_name = "usecases"
    paginate_by = 12

    def get_queryset(self):
        return UseCasePage.objects.prefetch_related("top_picks")


class UseCasePageDetailView(DetailView):
    model = UseCasePage
    template_name = "catalog/usecase_detail.html"
    context_object_name = "usecase"

    def get_queryset(self):
        return UseCasePage.objects.prefetch_related("top_picks__brand")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["meta"] = _build_meta(self.object)
        return ctx


# ---------------------------------------------------------------------------
# Affiliate redirect
# ---------------------------------------------------------------------------
class AffiliateRedirectView(View):
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        link = AffiliateLink.objects.filter(product=product).first()

        if link:
            # Atomically increment click_count
            AffiliateLink.objects.filter(pk=link.pk).update(
                click_count=F("click_count") + 1
            )
            # Log the click
            ClickLog.objects.create(
                affiliate_link=link,
                referrer=request.META.get("HTTP_REFERER", "")[:200],
            )
            return redirect(link.affiliate_url)

        # Fallback: redirect to source URL if no affiliate link exists
        if product.source_url:
            return redirect(product.source_url)
        return redirect(product.get_absolute_url())


# ---------------------------------------------------------------------------
# Email subscribe (HTMX)
# ---------------------------------------------------------------------------
class SubscribeView(View):
    def post(self, request):
        email = request.POST.get("email", "").strip().lower()
        source_page = request.POST.get("source_page", "")[:255]

        if not email:
            return HttpResponse(
                '<span class="text-error">Email is required.</span>', status=400
            )

        try:
            validate_email(email)
        except ValidationError:
            return HttpResponse(
                '<span class="text-error">Invalid email address.</span>', status=400
            )

        _, created = EmailSubscriber.objects.get_or_create(
            email=email,
            defaults={"source_page": source_page, "is_active": True},
        )

        if not created:
            return HttpResponse('<span class="text-info">You\'re already subscribed!</span>')

        return HttpResponse('<span class="text-success">Thanks for subscribing! 🎉</span>')
