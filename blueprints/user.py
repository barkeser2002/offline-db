from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import db

user_bp = Blueprint('user', __name__)

@user_bp.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    if db.get_user_by_username(username):
        return jsonify({"error": "Username already exists"}), 400

    password_hash = generate_password_hash(password)
    user_id = db.create_user(username, email, password_hash)

    if user_id:
        session["user_id"] = user_id
        session["username"] = username
        return jsonify({"success": True, "user_id": user_id})

    return jsonify({"error": "Registration failed"}), 500

@user_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = db.get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return jsonify({"success": True})

    return jsonify({"error": "Invalid credentials"}), 401

@user_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@user_bp.route("/api/auth/me", methods=["GET"])
def me():
    if "user_id" in session:
        return jsonify({
            "logged_in": True,
            "user_id": session["user_id"],
            "username": session["username"]
        })
    return jsonify({"logged_in": False})

@user_bp.route("/api/user/history", methods=["GET", "POST"])
def history():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]

    if request.method == "POST":
        data = request.get_json()
        mal_id = data.get("mal_id")
        episode = data.get("episode")
        progress = data.get("progress", 0)

        # Get internal anime ID
        anime = db.get_anime_by_mal_id(mal_id)
        if not anime:
            return jsonify({"error": "Anime not found"}), 404

        db.update_watch_history(user_id, anime["id"], episode, progress)
        return jsonify({"success": True})

    else:
        limit = request.args.get("limit", 10, type=int)
        history_data = db.get_user_watch_history(user_id, limit)
        return jsonify(history_data)

@user_bp.route("/api/user/watchlist", methods=["GET", "POST"])
def watchlist():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]

    if request.method == "POST":
        data = request.get_json()
        mal_id = data.get("mal_id")
        status = data.get("status")

        anime = db.get_anime_by_mal_id(mal_id)
        if not anime:
            return jsonify({"error": "Anime not found"}), 404

        db.update_watchlist(user_id, anime["id"], status)
        return jsonify({"success": True})

    else:
        watchlist_data = db.get_user_watchlist(user_id)
        return jsonify(watchlist_data)
