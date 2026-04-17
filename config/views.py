from django.views.generic import TemplateView


class HomePageView(TemplateView):
    """Главная страница проекта."""

    template_name = "home.html"