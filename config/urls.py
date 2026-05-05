"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from catalog.sitemaps import ComparisonSitemap, ProductSitemap, UseCasePageSitemap


@csrf_exempt
def healthcheck(_request):
    """Liveness probe — no DB query, no host check, no template render."""
    return HttpResponse("ok", content_type="text/plain")

sitemaps = {
    "products": ProductSitemap,
    "comparisons": ComparisonSitemap,
    "usecases": UseCasePageSitemap,
}

urlpatterns = [
    path("healthz", healthcheck),
    path("admin/", admin.site.urls),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots-txt",
    ),
    path("", include("catalog.urls")),
    path("", include("pages.urls")),
]
