from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("affiliate-disclosure/", views.PlaceholderPage.as_view(page_title="Affiliate Disclosure"), name="affiliate-disclosure"),
    path("contact/", views.PlaceholderPage.as_view(page_title="Contact"), name="contact"),
]
