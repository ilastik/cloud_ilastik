from django.core.management.base import BaseCommand
from allauth.socialaccount import models


class Command(BaseCommand):
    help = "Register OIDC client to process user auth through HBP"

    def add_arguments(self, parser):
        parser.add_argument("client_id", type=str)
        parser.add_argument("client_secret", type=str)

    def handle(self, *args, **options):
        app = models.SocialApp.objects.create(
            provider="hbp_oauth2", name="HBP Client", client_id=options["client_id"], secret=options["client_secret"]
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully created social app '{app.id}'"))
