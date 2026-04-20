from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import (
    CleaningEventForm,
    CustomEventForm,
    FeedingEventForm,
    MeasurementEventForm,
    PetForm,
    SheddingEventForm,
)
from .models import Event, Pet
from .services import (
    build_event_row_context,
    build_pet_card_context,
    get_measurement_comment_lines,
    get_owner_display,
    get_pet_age_display,
    get_upcoming_pet_tasks,
    pet_can_handle,
    pet_is_in_shedding,
)


class ModeratorAccessMixin:
    moderator_group_name = "Moderators"

    def is_moderator(self) -> bool:
        user = self.request.user
        if not user.is_authenticated:
            return False
        return user.is_superuser or user.groups.filter(name=self.moderator_group_name).exists()

    def is_owner(self, obj) -> bool:
        return getattr(obj, "owner_id", None) == self.request.user.id

    def can_edit_pet(self, pet: Pet) -> bool:
        return self.is_moderator() or self.is_owner(pet)

    def can_view_pet(self, pet: Pet) -> bool:
        if pet.is_public:
            return True
        return self.is_moderator() or self.is_owner(pet)


class PetEditPermissionMixin(ModeratorAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.can_edit_pet(obj):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PetDetailPermissionMixin(ModeratorAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_view_pet(self.object):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class EventOwnerOrModeratorMixin(ModeratorAccessMixin):
    def get_queryset(self):
        qs = Event.objects.select_related("pet", "owner").order_by("-event_datetime")
        if self.is_moderator():
            return qs
        return qs.filter(owner=self.request.user)


class PetListView(LoginRequiredMixin, ModeratorAccessMixin, ListView):
    model = Pet
    template_name = "pets/pet_list.html"
    context_object_name = "pets"

    def get_queryset(self):
        qs = Pet.objects.select_related("owner").prefetch_related("events").order_by("-created_at")
        if self.is_moderator():
            return qs
        return qs.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pet_cards"] = [build_pet_card_context(pet, self.request.user) for pet in context["pets"]]
        return context


class PetDetailView(PetDetailPermissionMixin, DetailView):
    model = Pet
    template_name = "pets/pet_detail.html"
    context_object_name = "pet"

    def get_queryset(self):
        return Pet.objects.select_related("owner").prefetch_related("events")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pet = self.object
        events = pet.events.all().order_by("-event_datetime")[:6]
        context["pet_age_display"] = get_pet_age_display(pet.birth_date)
        context["owner_display"] = get_owner_display(pet.owner)
        context["is_owner"] = self.request.user.id == pet.owner_id
        context["can_edit_pet"] = self.can_edit_pet(pet)
        context["can_handle"] = pet_can_handle(pet)
        context["is_in_shedding"] = pet_is_in_shedding(pet)
        context["upcoming_tasks"] = get_upcoming_pet_tasks(pet)
        context["is_public_view"] = not self.can_edit_pet(pet)
        context["pet_event_rows"] = [
            build_event_row_context(event) for event in events
        ]
        return context


class PetCreateView(LoginRequiredMixin, CreateView):
    model = Pet
    form_class = PetForm
    template_name = "pets/pet_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class PetUpdateView(LoginRequiredMixin, PetEditPermissionMixin, UpdateView):
    model = Pet
    form_class = PetForm
    template_name = "pets/pet_form.html"

    def get_queryset(self):
        return Pet.objects.select_related("owner")


class PetDeleteView(LoginRequiredMixin, PetEditPermissionMixin, DeleteView):
    model = Pet
    template_name = "pets/pet_confirm_delete.html"
    success_url = reverse_lazy("pets:pet_list")

    def get_queryset(self):
        return Pet.objects.select_related("owner")


EVENT_FORM_MAP = {
    Event.EventType.FEEDING: FeedingEventForm,
    Event.EventType.SHEDDING: SheddingEventForm,
    Event.EventType.CLEANING: CleaningEventForm,
    Event.EventType.MEASUREMENT: MeasurementEventForm,
    Event.EventType.CUSTOM: CustomEventForm,
}


class EventListView(LoginRequiredMixin, EventOwnerOrModeratorMixin, ListView):
    model = Event
    template_name = "pets/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        qs = super().get_queryset()

        selected_pet_ids = self.request.GET.getlist("pet")
        selected_event_types = self.request.GET.getlist("event_type")
        ordering = self.request.GET.get("ordering", "-event_datetime")

        if selected_pet_ids:
            qs = qs.filter(pet_id__in=selected_pet_ids)

        if selected_event_types:
            qs = qs.filter(event_type__in=selected_event_types)

        allowed_ordering = {
            "event_datetime": "event_datetime",
            "-event_datetime": "-event_datetime",
        }
        qs = qs.order_by(allowed_ordering.get(ordering, "-event_datetime"))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pets_qs = Pet.objects.select_related("owner").order_by("name")
        if not self.is_moderator():
            pets_qs = pets_qs.filter(owner=self.request.user)

        current_ordering = self.request.GET.get("ordering", "-event_datetime")
        next_ordering = "event_datetime" if current_ordering == "-event_datetime" else "-event_datetime"

        context["filter_pets"] = pets_qs
        context["selected_pet_ids"] = self.request.GET.getlist("pet")
        context["selected_event_types"] = self.request.GET.getlist("event_type")
        context["current_ordering"] = current_ordering
        context["next_ordering"] = next_ordering
        context["event_rows"] = [build_event_row_context(event) for event in context["events"]]
        return context


class EventDetailView(LoginRequiredMixin, EventOwnerOrModeratorMixin, DetailView):
    model = Event
    template_name = "pets/event_detail.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["measurement_comment_lines"] = get_measurement_comment_lines(self.object)
        return context


class EventCreateView(LoginRequiredMixin, ModeratorAccessMixin, CreateView):
    model = Event
    template_name = "pets/event_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.event_type = self.kwargs["event_type"]
        if self.event_type not in EVENT_FORM_MAP:
            raise Http404("Unknown event type")
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return EVENT_FORM_MAP[self.event_type]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["is_moderator"] = self.is_moderator()
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["event_type"] = self.event_type
        pet_id = self.request.GET.get("pet")
        if pet_id:
            initial["pet"] = pet_id
        return initial

    def form_valid(self, form):
        form.instance.owner = form.cleaned_data["pet"].owner if self.is_moderator() else self.request.user
        form.instance.event_type = self.event_type
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, EventOwnerOrModeratorMixin, UpdateView):
    model = Event
    template_name = "pets/event_form.html"

    def get_form_class(self):
        return EVENT_FORM_MAP[self.get_object().event_type]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["is_moderator"] = self.is_moderator()
        return kwargs

    def form_valid(self, form):
        form.instance.owner = form.cleaned_data["pet"].owner if self.is_moderator() else self.request.user
        return super().form_valid(form)


class EventDeleteView(LoginRequiredMixin, EventOwnerOrModeratorMixin, DeleteView):
    model = Event
    template_name = "pets/event_confirm_delete.html"
    success_url = reverse_lazy("pets:event_list")
