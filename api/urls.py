from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import GameViewSet

router = DefaultRouter()
router.register(r"games", GameViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
