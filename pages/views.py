from datetime import datetime

from django.views.generic import TemplateView


class PlaceholderPage(TemplateView):
    template_name = "pages/placeholder.html"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = self.page_title
        ctx["year"] = datetime.now().year
        return ctx
