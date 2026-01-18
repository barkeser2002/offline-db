from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import db

user_bp = Blueprint("user", __name__)


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
        return jsonify(
            {
                "logged_in": True,
                "user_id": session["user_id"],
                "username": session["username"],
            }
        )
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


@user_bp.route("/api/user/stats", methods=["GET"])
def user_stats():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    stats = db.get_user_stats(session["user_id"])
    return jsonify(db.serialize_for_json(stats))


@user_bp.route("/api/user/favorite", methods=["POST"])
def toggle_fav():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    mal_id = data.get("mal_id")
    if not mal_id:
        return jsonify({"error": "mal_id required"}), 400

    action = db.toggle_favorite(session["user_id"], mal_id)
    if not action:
        return jsonify({"error": "Action failed"}), 500

    return jsonify({"success": True, "action": action})


@user_bp.route("/api/user/favorite/check")
def check_fav():
    if "user_id" not in session:
        return jsonify({"is_favorite": False})

    mal_id = request.args.get("mal_id", type=int)
    if not mal_id:
        return jsonify({"is_favorite": False})

    return jsonify({"is_favorite": db.is_favorite(session["user_id"], mal_id)})


@user_bp.route("/api/user/favorites")
def get_favorites():
    user_id = request.args.get("user_id", type=int)
    if not user_id and "user_id" in session:
        user_id = session["user_id"]

    if not user_id:
        return jsonify([])

    favs = db.get_user_favorites(user_id)
    return jsonify(db.serialize_for_json(favs))


@user_bp.route("/api/user/activity")
def get_activity():
    user_id = request.args.get("user_id", type=int)
    limit = request.args.get("limit", 20, type=int)

    activities = db.get_user_activity(user_id, limit)
    return jsonify(db.serialize_for_json(activities))


@user_bp.route("/api/user/follow", methods=["POST"])
def follow_user():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    target_user_id = data.get("target_user_id")
    if not target_user_id:
        return jsonify({"error": "target_user_id required"}), 400

    action = db.toggle_follow(session["user_id"], target_user_id)
    if not action:
        return jsonify({"error": "Cannot follow yourself or user not found"}), 400

    return jsonify({"success": True, "action": action})


@user_bp.route("/api/user/social-feed")
def get_social_feed():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    limit = request.args.get("limit", 50, type=int)
    feed = db.get_social_feed(session["user_id"], limit)
    return jsonify(db.serialize_for_json(feed))


@user_bp.route("/api/community/leaderboard")
def get_leaderboard():
    limit = request.args.get("limit", 10, type=int)
    leaderboard = db.get_top_watchers(limit)
    return jsonify(db.serialize_for_json(leaderboard))
