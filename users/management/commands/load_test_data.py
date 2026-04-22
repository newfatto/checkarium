from datetime import timedelta

from django.contrib.auth.models import Group
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.utils import timezone

from pets.models import Event, Pet
from users.models import CustomUser


class Command(BaseCommand):
    """Загружает фикстуру с демо-пользователями и питомцами и создаёт демо-события."""

    help = "Быстро заполняет базу демо-данными для Checkarium."

    fixture_name = "demo_data"
    moderator_group_name = "Moderators"

    demo_credentials = {
        "user@user.user": "Testpass123!",
        "user1@user.user": "Testpass123!",
        "user2@user.user": "Testpass123!",
        "test@test.com": "Testpass123!",
        "moderator@checkarium.local": "Moderator123!",
    }

    demo_emails = tuple(demo_credentials.keys())
    moderator_emails = ("moderator@checkarium.local",)

    def add_arguments(self, parser) -> None:
        """Добавляет аргументы management-команды."""
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить старые демо-данные перед повторной загрузкой.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        """Запускает загрузку демо-данных."""
        if options["reset"]:
            self._reset_demo_data()

        self._load_fixture_if_needed()
        self._set_demo_passwords()
        self._setup_moderator_group()
        self._rebuild_demo_events()

        self.stdout.write(self.style.SUCCESS("Демо-данные успешно загружены."))
        self.stdout.write("")
        self.stdout.write("Тестовые аккаунты:")
        for email, password in self.demo_credentials.items():
            self.stdout.write(f"  {email} / {password}")

    def _reset_demo_data(self) -> None:
        """Удаляет старые демо-данные."""
        CustomUser.objects.filter(email__in=self.demo_emails).delete()
        self.stdout.write("Старые демо-данные удалены.")

    def _load_fixture_if_needed(self) -> None:
        """Загружает фикстуру, если демо-пользователи ещё не созданы."""
        existing_count = CustomUser.objects.filter(email__in=self.demo_emails).count()

        if existing_count == len(self.demo_emails):
            self.stdout.write("Фикстура уже загружена, демо-пользователи существуют.")
            return

        if existing_count:
            CustomUser.objects.filter(email__in=self.demo_emails).delete()

        call_command("loaddata", self.fixture_name, verbosity=0)
        self.stdout.write(f"Фикстура '{self.fixture_name}' загружена.")

    def _set_demo_passwords(self) -> None:
        """Проставляет известные пароли демо-пользователям поверх хэшей из фикстуры."""
        for email, password in self.demo_credentials.items():
            user = CustomUser.objects.get(email=email)
            user.set_password(password)
            user.save(update_fields=["password"])

        self.stdout.write("Пароли демо-пользователей обновлены.")

    def _setup_moderator_group(self) -> None:
        """Создаёт группу модераторов и добавляет в неё демо-модераторов."""
        moderator_group, _ = Group.objects.get_or_create(name=self.moderator_group_name)

        moderators = CustomUser.objects.filter(email__in=self.moderator_emails)
        for moderator in moderators:
            moderator.groups.add(moderator_group)

        self.stdout.write("Группа Moderators настроена.")

    def _rebuild_demo_events(self) -> None:
        """Удаляет старые события демо-питомцев и создаёт новые, привязанные к текущей дате."""
        pets = Pet.objects.filter(owner__email__in=self.demo_emails)
        Event.objects.filter(pet__in=pets).delete()

        now = timezone.now().replace(second=0, microsecond=0)
        pet_map = {pet.name: pet for pet in pets.select_related("owner")}

        if "Кукуруза" in pet_map:
            self._seed_corn_snake_events(pet_map["Кукуруза"], now)

        if "Точка" in pet_map:
            self._seed_gecko_events(pet_map["Точка"], now)

        if "Пиксель" in pet_map:
            self._seed_frog_events(pet_map["Пиксель"], now)

        if "Тортилла" in pet_map:
            self._seed_turtle_events(pet_map["Тортилла"], now)

        if "Арахна" in pet_map:
            self._seed_spider_events(pet_map["Арахна"], now)

        if "Сатурн" in pet_map:
            self._seed_scorpion_events(pet_map["Сатурн"], now)

        if "Сладкая Булочка" in pet_map:
            self._seed_ball_python_events(pet_map["Сладкая Булочка"], now)

        self.stdout.write("Демо-события созданы.")

    def _create_event(
        self,
        *,
        pet: Pet,
        event_type: str,
        dt,
        comment: str = "",
        repeat_after_days: int | None = None,
        no_handling_days: int | None = None,
        title: str = "",
        weight_grams: int | None = None,
        length_cm: int | None = None,
    ) -> Event:
        """Создаёт одно событие для питомца."""
        return Event.objects.create(
            owner=pet.owner,
            pet=pet,
            event_type=event_type,
            title=title,
            event_datetime=dt,
            comment=comment,
            repeat_after_days=repeat_after_days,
            no_handling_days=no_handling_days,
            weight_grams=weight_grams,
            length_cm=length_cm,
        )

    def _seed_corn_snake_events(self, pet: Pet, now) -> None:
        """Создаёт события для маисового полоза."""
        self._create_event(
            pet=pet,
            event_type=Event.EventType.MEASUREMENT,
            dt=now - timedelta(days=45),
            weight_grams=32,
            length_cm=48,
            comment="Первое контрольное измерение.",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.MEASUREMENT,
            dt=now - timedelta(days=7),
            weight_grams=38,
            length_cm=55,
            comment="После линьки и кормления.",
            repeat_after_days=30,
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.FEEDING,
            dt=now - timedelta(days=3),
            repeat_after_days=10,
            no_handling_days=2,
            comment="1 мышь-голыш.",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.CLEANING,
            dt=now - timedelta(days=9),
            repeat_after_days=14,
            comment="Полная уборка террариума.",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.CUSTOM,
            dt=now - timedelta(days=20),
            title="Осмотр",
            comment="Проверка состояния после адаптации.",
        )

    def _seed_gecko_events(self, pet: Pet, now) -> None:
        """Создаёт события для эублефара."""
        self._create_event(
            pet=pet,
            event_type=Event.EventType.MEASUREMENT,
            dt=now - timedelta(days=12),
            weight_grams=54,
            length_cm=22,
            repeat_after_days=21,
            comment="Плановое измерение.",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.FEEDING,
            dt=now - timedelta(days=1),
            repeat_after_days=5,
            no_handling_days=2,
            comment="Сверчки и кальций.",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.CLEANING,
            dt=now - timedelta(days=6),
            repeat_after_days=7,
            comment="Локальная уборка.",
        )

    def _seed_frog_events(self, pet: Pet, now) -> None:
        """Создаёт события для лягушки."""
        self._create_event(
            pet=pet,
            event_type=Event.EventType.SHEDDING,
            dt=now - timedelta(days=2),
            no_handling_days=5,
            comment="Идёт линька, лучше не беспокоить.",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.FEEDING,
            dt=now - timedelta(days=4),
            repeat_after_days=6,
            no_handling_days=1,
            comment="Мелкие сверчки.",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.CUSTOM,
            dt=now - timedelta(days=18),
            title="Переезд",
            comment="Пересажен в новый контейнер.",
        )

    def _seed_turtle_events(self, pet: Pet, now) -> None:
        """Создаёт события для черепахи."""
        self._create_event(
            pet=pet,
            event_type=Event.EventType.MEASUREMENT,
            dt=now - timedelta(days=30),
            weight_grams=410,
            length_cm=18,
            repeat_after_days=60,
            comment="Контроль роста.",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.CLEANING,
            dt=now - timedelta(days=15),
            repeat_after_days=30,
            comment="Чистка акватеррариума.",
        )

    def _seed_spider_events(self, pet: Pet, now) -> None:
        """Создаёт события для паука."""
        self._create_event(
            pet=pet,
            event_type=Event.EventType.FEEDING,
            dt=now - timedelta(days=4),
            repeat_after_days=7,
            no_handling_days=1,
            comment="Кормовые тараканы.",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.CUSTOM,
            dt=now - timedelta(days=40),
            title="Пересадка",
            comment="Полная замена субстрата.",
        )

    def _seed_scorpion_events(self, pet: Pet, now) -> None:
        """Создаёт события для скорпиона."""
        self._create_event(
            pet=pet,
            event_type=Event.EventType.CUSTOM,
            dt=now - timedelta(days=25),
            title="Передача",
            comment="Питомец передан другому владельцу.",
        )

    def _seed_ball_python_events(self, pet: Pet, now) -> None:
        """Создаёт события для Сладкой Булочки по данным из dump-файла."""
        self._create_event(
            pet=pet,
            event_type=Event.EventType.CUSTOM,
            dt=now - timedelta(days=1, hours=3),
            title="Поездка",
            comment="Съездили на фотосессию, ждём фото",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.MEASUREMENT,
            dt=now - timedelta(hours=1, minutes=20),
            weight_grams=222,
            length_cm=91,
            repeat_after_days=30,
            comment="",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.MEASUREMENT,
            dt=now - timedelta(hours=1),
            weight_grams=223,
            length_cm=92,
            repeat_after_days=15,
            comment="",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.CLEANING,
            dt=now - timedelta(minutes=20),
            repeat_after_days=15,
            comment="",
        )
        self._create_event(
            pet=pet,
            event_type=Event.EventType.FEEDING,
            dt=now - timedelta(minutes=5),
            repeat_after_days=7,
            no_handling_days=3,
            comment="Съела мышь",
        )
