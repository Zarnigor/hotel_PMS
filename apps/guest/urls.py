from rest_framework.routers import SimpleRouter

from apps.guest.views import GuestViewSet

router = SimpleRouter()
router.register('guests', GuestViewSet, basename='guest')

urlpatterns = router.urls
