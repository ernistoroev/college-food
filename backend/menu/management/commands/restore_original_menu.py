import json
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from menu.models import Category, Dish
from menu.management.commands.import_dishes import DISHES


class Command(BaseCommand):
    help = "Безопасное восстановление исходного меню без перезаписи существующих блюд"

    @transaction.atomic
    def handle(self, *args, **options):
        seed_dir = settings.BASE_DIR / "menu" / "seed_images"
        manifest_path = seed_dir / "manifest.json"

        if not manifest_path.is_file():
            raise CommandError(f"Не найден файл: {manifest_path}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        categories = {}
        for order, name in enumerate(
            ["Горячее", "Супы", "Салаты", "Выпечка", "Напитки"], start=1
        ):
            category, _ = Category.objects.get_or_create(
                name=name,
                defaults={"order": order},
            )
            categories[name] = category

        created_count = 0
        existing_count = 0
        photo_count = 0

        for category_name, name, price, weight, portions, description in DISHES:
            category = categories[category_name]

            dish, created = Dish.objects.get_or_create(
                category=category,
                name=name,
                defaults={
                    "description": description,
                    "price": price,
                    "weight": weight,
                    "weight_unit": "мл" if category_name == "Напитки" else "г",
                    "portions_today": portions,
                    "is_available": True,
                },
            )

            if created:
                created_count += 1
            else:
                existing_count += 1

            if dish.image:
                continue

            photo = next(
                (
                    row for row in manifest
                    if row.get("name") == name
                    and row.get("category") == category_name
                ),
                None,
            )

            if not photo:
                continue

            image_path = (seed_dir / photo["file"]).resolve()

            if not image_path.is_relative_to(seed_dir.resolve()):
                raise CommandError(f"Недопустимый путь фотографии: {photo['file']}")

            if not image_path.is_file():
                raise CommandError(f"Фотография не найдена: {image_path}")

            with image_path.open("rb") as image_file:
                dish.image.save(image_path.name, File(image_file), save=True)

            photo_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Готово. Создано блюд: {created_count}; "
            f"уже существовало: {existing_count}; "
            f"добавлено фотографий: {photo_count}."
        ))
