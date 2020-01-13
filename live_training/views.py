from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings


@login_required(login_url="/accounts/hbp_oauth2/login")
def training_page(request):
    return render(request, "live_training/live_training.html", {"TRAINING_API_URL": settings.TRAINING_API_URL})
