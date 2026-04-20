from django.utils.deprecation import MiddlewareMixin

from .timezone_services import activate_user_timezone


class UserTimezoneMiddleware(MiddlewareMixin):
    """Активирует часовой пояс авторизованного пользователя на время запроса."""

    def process_request(self, request):
        activate_user_timezone(getattr(request, "user", None))
