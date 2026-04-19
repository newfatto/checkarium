from django.urls import path

from .apps import PetsConfig
from .views import (
    PetListView,
    PetDetailView,
    PetCreateView,
    PetUpdateView,
    PetDeleteView,
    EventListView,
    EventDetailView,
    EventCreateView,
    EventUpdateView,
    EventDeleteView,
)

app_name = PetsConfig.name

urlpatterns = [
    path("", PetListView.as_view(), name="pet_list"),
    path("create/", PetCreateView.as_view(), name="pet_create"),
    path("<int:pk>/", PetDetailView.as_view(), name="pet_detail"),
    path("<int:pk>/update/", PetUpdateView.as_view(), name="pet_update"),
    path("<int:pk>/delete/", PetDeleteView.as_view(), name="pet_delete"),

    path("events/", EventListView.as_view(), name="event_list"),
    path("events/create/<str:event_type>/", EventCreateView.as_view(), name="event_create"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="event_detail"),
    path("events/<int:pk>/update/", EventUpdateView.as_view(), name="event_update"),
    path("events/<int:pk>/delete/", EventDeleteView.as_view(), name="event_delete"),
]