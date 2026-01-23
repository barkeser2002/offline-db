from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from content.sitemaps import AnimeSitemap, EpisodeSitemap, GenreSitemap
from users.views import profile_view, badges_list_view

sitemaps = {
    'anime': AnimeSitemap,
    'episodes': EpisodeSitemap,
    'genres': GenreSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    # Users API
    path('api/users/', include('users.urls')),
    # User Profile
    path('profile/', profile_view, name='profile'),
    path('badges/', badges_list_view, name='badges_list'),
    # Content API
    path('api/content/', include('content.api.urls')),
    # Content
    path('', include('content.urls')),
    # Billing
    path('billing/', include('billing.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
