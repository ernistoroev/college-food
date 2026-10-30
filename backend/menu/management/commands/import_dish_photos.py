import json
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from menu.models import Dish


class Command(BaseCommand):
    help = "Загрузить сохранённые фотографии блюд"

    def handle(self, *args, **options):
        folder = settings.BASE_DIR / "menu" / "seed_images"
        manifest = folder / "manifest.json"
        if not manifest.exists():
            raise CommandError("Не найден manifest.json")

        rows = json.loads(manifest.read_text(encoding="utf-8"))
        added = 0
        for row in rows:
            dish = Dish.objects.filter(
                name=row["name"],
                category__name=row["category"],
            ).first()
            if dish is None:
                self.stdout.write(f'Нет блюда: {row["name"]}')
                continue

            photo = (folder / row["file"]).resolve()
            if not photo.is_relative_to(folder.resolve()) or not photo.is_file():
                self.stdout.write(f'Нет файла: {row["file"]}')
                continue

            if dish.image and dish.image.storage.exists(dish.image.name):
                continue

            with photo.open("rb") as source:
                dish.image.save(Path(row["file"]).name, File(source), save=True)
            added += 1

        self.stdout.write(self.style.SUCCESS(f"Добавлено фото: {added}"))
