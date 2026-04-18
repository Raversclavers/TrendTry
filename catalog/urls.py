from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("trending/", views.TrendingListView.as_view(), name="trending"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("brands/", views.BrandListView.as_view(), name="brands"),
    path("brands/<slug:slug>/", views.BrandDetailView.as_view(), name="brand-detail"),
    path("compare/", views.ComparisonListView.as_view(), name="comparisons"),
    path("compare/<slug:slug>/", views.ComparisonDetailView.as_view(), name="comparison-detail"),
    path("best/", views.UseCaseListView.as_view(), name="usecases"),
    path("best/<slug:slug>/", views.UseCasePageDetailView.as_view(), name="usecase-detail"),
    path("go/<slug:slug>/", views.AffiliateRedirectView.as_view(), name="affiliate-go"),
    path("subscribe/", views.SubscribeView.as_view(), name="subscribe"),
]
