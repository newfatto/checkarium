from django.views.generic import TemplateView

from pets.models import Pet
from pets.services import build_pet_card_context


class HomePageView(TemplateView):
    """Главная страница проекта."""

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pets = (
            Pet.objects.filter(is_public=True)
            .select_related("owner")
            .prefetch_related("events")
            .order_by("-created_at")
        )
        context["public_pet_cards"] = [build_pet_card_context(pet, self.request.user) for pet in pets]
        return context
