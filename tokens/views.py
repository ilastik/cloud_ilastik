from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.authtoken import models


@login_required(login_url="/accounts/hbp_oauth2/login")
def show_token(request):
    token, _ = models.Token.objects.get_or_create(user=request.user)

    return render(request, "tokens/token.html", {"token": token.key})
