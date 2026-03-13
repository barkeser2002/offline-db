#!/bin/bash
USE_SQLITE=True DJANGO_SECRET_KEY=dummy SHOPIER_SECRET=dummy python -m pytest --cov=scraper_module scraper_module/tests/
