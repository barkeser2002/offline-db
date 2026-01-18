from .models import SiteSettings

def site_settings(request):
    try:
        return {
            'site_settings': SiteSettings.get_settings()
        }
    except:
        return {}
