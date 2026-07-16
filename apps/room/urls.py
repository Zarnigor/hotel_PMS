from rest_framework.routers import DefaultRouter, SimpleRouter

from apps.room.views import RoomTypeBaseViewSet, RoomTypeViewSet, RoomViewSet

router = SimpleRouter()
router.register('room-type-bases', RoomTypeBaseViewSet, basename='room-type-base')
router.register('room-types', RoomTypeViewSet, basename='room-type')
router.register('rooms', RoomViewSet, basename='room')

urlpatterns = router.urls