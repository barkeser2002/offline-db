from django.test import TestCase
from django.apps import apps
from content.apps import ContentConfig

class ContentConfigTests(TestCase):
    def test_apps_registry(self):
        """Test that the content app is correctly registered in the apps registry."""
        app_config = apps.get_app_config('content')
        self.assertEqual(app_config.name, 'content')
        self.assertTrue(issubclass(type(app_config), ContentConfig))

    def test_models_import(self):
        """Test that critical models are available via the app registry."""
        app_config = apps.get_app_config('content')
        models = app_config.get_models()
        model_names = [m.__name__ for m in models]

        self.assertIn('Anime', model_names)
        self.assertIn('Episode', model_names)
        self.assertIn('VideoFile', model_names)
