from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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


class ModeratorAccessMixin:
    moderator_group_name = "Moderators"

    def is_moderator(self) -> bool:
        user = self.request.user
        return user.is_superuser or user.groups.filter(name=self.moderator_group_name).exists()


class OwnerOrModeratorQuerysetMixin(ModeratorAccessMixin):
    model = None

    def get_queryset(self):
        qs = self.model.objects.all()
        if self.is_moderator():
            return qs
        return qs.filter(owner=self.request.user)


class OwnerOrModeratorObjectMixin(OwnerOrModeratorQuerysetMixin):
    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        return super().get_object(queryset=queryset)


# ---------------- PETS ----------------

class PetListView(LoginRequiredMixin, OwnerOrModeratorQuerysetMixin, ListView):
    model = Pet
    template_name = "pets/pet_list.html"
    context_object_name = "pets"


class PetDetailView(LoginRequiredMixin, OwnerOrModeratorObjectMixin, DetailView):
    model = Pet
    template_name = "pets/pet_detail.html"
    context_object_name = "pet"


class PetCreateView(LoginRequiredMixin, CreateView):
    model = Pet
    form_class = PetForm
    template_name = "pets/pet_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class PetUpdateView(LoginRequiredMixin, OwnerOrModeratorObjectMixin, UpdateView):
    model = Pet
    form_class = PetForm
    template_name = "pets/pet_form.html"


class PetDeleteView(LoginRequiredMixin, OwnerOrModeratorObjectMixin, DeleteView):
    model = Pet
    template_name = "pets/pet_confirm_delete.html"
    success_url = reverse_lazy("pets:pet_list")


# ---------------- EVENTS ----------------

EVENT_FORM_MAP = {
    Event.EventType.FEEDING: FeedingEventForm,
    Event.EventType.SHEDDING: SheddingEventForm,
    Event.EventType.CLEANING: CleaningEventForm,
    Event.EventType.MEASUREMENT: MeasurementEventForm,
    Event.EventType.CUSTOM: CustomEventForm,
}


class EventListView(LoginRequiredMixin, ModeratorAccessMixin, ListView):
    model = Event
    template_name = "pets/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        qs = Event.objects.select_related("pet", "owner").order_by("-event_datetime")

        if not self.is_moderator():
            qs = qs.filter(owner=self.request.user)

        pet_id = self.request.GET.get("pet")
        event_type = self.request.GET.get("event_type")
        ordering = self.request.GET.get("ordering")

        if pet_id:
            qs = qs.filter(pet_id=pet_id)

        if event_type:
            qs = qs.filter(event_type=event_type)

        allowed_ordering = {
            "event_datetime": "event_datetime",
            "-event_datetime": "-event_datetime",
            "created_at": "created_at",
            "-created_at": "-created_at",
        }
        if ordering in allowed_ordering:
            qs = qs.order_by(allowed_ordering[ordering])

        return qs


class EventDetailView(LoginRequiredMixin, OwnerOrModeratorObjectMixin, DetailView):
    model = Event
    template_name = "pets/event_detail.html"
    context_object_name = "event"


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
        form.instance.owner = self.request.user if not self.is_moderator() else form.cleaned_data["pet"].owner
        form.instance.event_type = self.event_type
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, OwnerOrModeratorObjectMixin, UpdateView):
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
        if self.is_moderator():
            form.instance.owner = form.cleaned_data["pet"].owner
        else:
            form.instance.owner = self.request.user
        return super().form_valid(form)


class EventDeleteView(LoginRequiredMixin, OwnerOrModeratorObjectMixin, DeleteView):
    model = Event
    template_name = "pets/event_confirm_delete.html"
    success_url = reverse_lazy("pets:event_list")