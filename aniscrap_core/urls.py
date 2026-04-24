from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from content.views import AnimeViewSet, EpisodeViewSet, HomeViewSet
from apps.watchparty.views import RoomViewSet
from users.views import NotificationViewSet, UserBadgeViewSet, WatchLogViewSet, UserProfileAPIView, CustomTokenObtainPairView

from rest_framework.routers import SimpleRouter

# Setup DRF Router
router = SimpleRouter()
router.register(r'anime', AnimeViewSet)
router.register(r'episodes', EpisodeViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'user-badges', UserBadgeViewSet, basename='user-badges')
router.register(r'watch-history', WatchLogViewSet, basename='watch-history')
router.register(r'watch-parties', RoomViewSet)

# Create a separate router or manual path for ViewSet-as-view if needed, 
# but HomeViewSet is simple enough to map manually or use router with basename.
router.register(r'home', HomeViewSet, basename='home')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('content.urls')),
    
    # API Handlers
    path('api/v1/', include(router.urls)),
    path('api/v1/profile/', UserProfileAPIView.as_view(), name='user-profile'),
    
    # Auth (JWT)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Billing API (Assuming it follows API structure)
    path('api/billing/', include('billing.urls')),

    # Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
