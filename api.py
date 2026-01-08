#!/usr/bin/env python3
"""
Anime Offline DB - Web API & Player
"""

from flask import Flask
from config import API_HOST, API_PORT
from blueprints.ui import ui_bp
from blueprints.api import api_bp

app = Flask(__name__)

app.register_blueprint(ui_bp)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           🎬 Anime Offline DB - Web API                     ║
╠════════════════════════════════════════════════════════════╣
║  http://{API_HOST}:{API_PORT}/                              ║
║  http://{API_HOST}:{API_PORT}/player?mal_id=1               ║
║  http://{API_HOST}:{API_PORT}/api/stream/1/1                ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host=API_HOST, port=API_PORT, debug=True, threaded=True)
