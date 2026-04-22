from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from config.views import HomePageView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", HomePageView.as_view(), name="home"),
    path("users/", include("users.urls", namespace="users")),
    path("pets/", include("pets.urls", namespace="pets")),
]

urlpatterns += [
    re_path(
        r"^static/(?P<path>.*)$",
        serve,
        {"document_root": settings.STATIC_ROOT},
    )
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
