"""
Management command: seed_fake_data

Joylashuv: apps/management/commands/seed_fake_data.py

Katalog (spravochnik) ma'lumotlari — belgilangan, cheklangan hajmda:
    - RoomTypeBase   (~100 ta aniq, noyob kategoriya)
    - RoomType       (aniq xona turlari, bazaviy kategoriya + wing bilan noyob nom)

Tranzaksion ma'lumotlar — --count orqali boshqariladi (masalan 1_000_000):
    - Room
    - RoomInventory
    - Reservation

Ishlatish:
    python manage.py seed_fake_data
    python manage.py seed_fake_data --count 1000000
    python manage.py seed_fake_data --count 1000000 --flush   # avval eski fake datalarni tozalaydi

Talab: pip install Faker
"""

import itertools
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from faker import Faker

from apps.room.models import RoomTypeBase, RoomType, Room, RoomInventory
from apps.reservation.models import Reservation

fake = Faker()

BULK_BATCH_SIZE = 5000  # bir martada DB'ga yuboriladigan yozuvlar soni

# --- RoomTypeBase uchun: taxminan 100 ta noyob kategoriya nomi ---
ROOM_BASE_ADJECTIVES = [
    "Standard", "Deluxe", "Superior", "Premium", "Executive", "Classic",
    "Comfort", "Grand", "Royal", "Elite", "Luxury", "Business", "Family",
    "Economy", "Panoramic", "Garden", "City", "Coastal", "Mountain",
    "Modern",
]  # 20 ta
ROOM_BASE_NOUNS = [
    "Room", "Suite", "Studio", "Apartment", "Penthouse", "Villa",
]  # 6 ta -> 120 ta kombinatsiya

ROOM_TYPE_BASE_NAMES = [
    f"{adj} {noun}" for adj, noun in itertools.product(ROOM_BASE_ADJECTIVES, ROOM_BASE_NOUNS)
][:100]  # aniq 100 ta

SPECIFIC_ROOM_TYPES = [
    "Standard Single Room", "Standard Double Room", "Standard Twin Room",
    "Deluxe Single Room", "Deluxe Double Room", "Deluxe Twin Room",
    "Superior Double Room", "Superior Twin Room",
    "Junior Suite", "Executive Suite", "Presidential Suite",
    "Family Room", "Family Suite",
    "Business Room", "Business Suite",
    "Panoramic View Room", "Garden View Room", "City View Room",
    "Sea View Room", "Mountain View Room",
    "Studio Room", "Penthouse Suite", "Economy Room",
    "Connecting Room", "Accessible Room", "Honeymoon Suite",
    "Royal Suite", "Grand Deluxe Room", "Comfort Room", "Premium Suite",
]  # 30 ta
WINGS_PER_COMBO = 10


def chunked_bulk_create(model, objs_iterable, batch_size=BULK_BATCH_SIZE, label=""):
    buffer = []
    total = 0
    for obj in objs_iterable:
        buffer.append(obj)
        if len(buffer) >= batch_size:
            model.objects.bulk_create(buffer, batch_size=batch_size)
            total += len(buffer)
            print(f"  {label}: {total} ta yaratildi...")
            buffer = []
    if buffer:
        model.objects.bulk_create(buffer, batch_size=batch_size)
        total += len(buffer)
    return total


class Command(BaseCommand):
    help = "PMS modellari uchun Faker orqali fake data generatsiya qiladi"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=500,
            help="Room, RoomInventory, Reservation uchun yaratiladigan yozuvlar soni (default: 500)",
        )
        parser.add_argument(
            "--flush", action="store_true",
            help="Yaratishdan oldin mavjud yozuvlarni (hard delete) tozalash",
        )

    def handle(self, *args, **options):
        count = options["count"]

        if options["flush"]:
            self.stdout.write(self.style.WARNING("Eski data tozalanmoqda..."))
            with transaction.atomic():
                Reservation.objects.all().delete()
                RoomInventory.objects.all().delete()
                Room.all_objects.all().delete()
                RoomType.all_objects.all().delete()
                RoomTypeBase.all_objects.all().delete()

        # Katalog ma'lumotlari — count'ga bog'liq emas, bitta transaction ichida
        with transaction.atomic():
            room_type_bases = self._seed_room_type_bases()
            room_types = self._seed_room_types(room_type_bases)

        rooms = self._seed_rooms(count, room_types)
        self._seed_room_inventory(count, room_types)
        self._seed_reservations(count, room_types, rooms)

        self.stdout.write(self.style.SUCCESS(
            f"Tayyor: {len(room_type_bases)} ta RoomTypeBase, {len(room_types)} ta RoomType, "
            f"{count} tagacha Room/RoomInventory/Reservation yaratildi."
        ))

    def _seed_room_type_bases(self):
        self.stdout.write(f"RoomTypeBase yaratilmoqda ({len(ROOM_TYPE_BASE_NAMES)} ta)...")
        objs = [
            RoomTypeBase(
                name=name,
                description=fake.sentence(nb_words=12),
            )
            for name in ROOM_TYPE_BASE_NAMES
        ]
        RoomTypeBase.objects.bulk_create(objs, batch_size=500)
        return list(RoomTypeBase.objects.all())

    def _seed_room_types(self, room_type_bases):
        self.stdout.write("RoomType yaratilmoqda...")
        objs = [
            RoomType(
                room_type_base=base,
                name=f"{specific_name} ({base.name}) - Wing {wing}",
                base_price=Decimal(random.randrange(150, 1200)) * Decimal("100"),
            )
            for base, specific_name in itertools.product(room_type_bases, SPECIFIC_ROOM_TYPES)
            for wing in range(1, WINGS_PER_COMBO + 1)
        ]
        RoomType.objects.bulk_create(objs, batch_size=500)
        return list(RoomType.objects.all())

    def _seed_rooms(self, count, room_types):
        self.stdout.write(f"Room yaratilmoqda ({count} ta)...")
        rooms_per_floor = 20
        floors_per_building = 30
        rooms_per_building = rooms_per_floor * floors_per_building
        statuses = [c[0] for c in Room.Status.choices]

        def gen():
            for i in range(count):
                building = i // rooms_per_building + 1
                rem = i % rooms_per_building
                floor = rem // rooms_per_floor + 1
                unit = rem % rooms_per_floor + 1
                number = f"{building}-{floor:02d}{unit:02d}"
                yield Room(
                    room_number=number,
                    room_type=random.choice(room_types),
                    status=random.choice(statuses),
                )

        chunked_bulk_create(Room, gen(), label="Room")
        return list(Room.objects.all().iterator(chunk_size=5000))

    def _seed_room_inventory(self, count, room_types):
        """
        (date, room_type) juftligi noyob bo'lishi kerak.
        """
        self.stdout.write("RoomInventory yaratilmoqda...")
        today = timezone.now().date()

        date_range_days = max(60, (count // max(len(room_types), 1)) + 30)
        dates = [today + timedelta(days=d) for d in range(-30, date_range_days)]

        all_pairs = list(itertools.product(dates, room_types))
        random.shuffle(all_pairs)

        target = min(count, len(all_pairs))
        if count > len(all_pairs):
            self.stdout.write(self.style.WARNING(
                f"So'ralgan {count} ta RoomInventory uchun yetarli noyob (sana, room_type) "
                f"juftligi yo'q, {target} tasi yaratiladi."
            ))

        def gen():
            for date, room_type in all_pairs[:target]:
                total = random.randint(5, 40)
                booked = random.randint(0, total)
                yield RoomInventory(
                    date=date,
                    room_type=room_type,
                    total_rooms=total,
                    booked_rooms=booked,
                )

        chunked_bulk_create(RoomInventory, gen(), label="RoomInventory")

    def _seed_reservations(self, count, room_types, rooms):
        self.stdout.write(f"Reservation yaratilmoqda ({count} ta)...")
        today = timezone.now().date()
        statuses = [c[0] for c in Reservation.Status.choices]
        rooms_count = len(rooms)

        def gen():
            for _ in range(count):
                check_in = today + timedelta(days=random.randint(-10, 90))
                check_out = check_in + timedelta(days=random.randint(1, 14))
                yield Reservation(
                    guest_name=fake.name()[:25].strip(),
                    room_type=random.choice(room_types),
                    assigned_room=rooms[random.randrange(rooms_count)] if random.random() > 0.2 else None,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    status=random.choice(statuses),
                )

        chunked_bulk_create(Reservation, gen(), label="Reservation")