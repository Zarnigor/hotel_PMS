from rest_framework.routers import DefaultRouter, SimpleRouter

from apps.room.views import RoomTypeBaseViewSet

router = SimpleRouter()
router.register('room-type-bases', RoomTypeBaseViewSet, basename='room-type-base')

urlpatterns = router.urls