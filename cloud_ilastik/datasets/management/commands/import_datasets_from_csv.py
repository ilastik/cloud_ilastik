import csv

from django.core.management.base import BaseCommand
from cloud_ilastik.datasets import models


class Command(BaseCommand):
    help = "Import datasets from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=str)

    def handle(self, *args, **options):
        datasets = []

        with open(options["input_file"], newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                datasets.append(
                    models.Dataset(
                        name=row["name"],
                        url=row["url"],
                        size_t=row["t"],
                        size_c=row["c"],
                        size_x=row["x"],
                        size_y=row["y"],
                        size_z=row["z"],
                    )
                )

        models.Dataset.objects.bulk_create(datasets)

        self.stdout.write(self.style.SUCCESS(f"Imported {len(datasets)} datasets"))
