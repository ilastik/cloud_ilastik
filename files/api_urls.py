from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("", views.FileViewset, basename="file")

urlpatterns = router.urls
