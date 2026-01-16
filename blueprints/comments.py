from flask import Blueprint, request, jsonify, session
import db

comments_bp = Blueprint('comments', __name__)

@comments_bp.route("/api/comments/<int:mal_id>/<int:episode>", methods=["GET"])
def get_comments(mal_id, episode):
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    comments = db.get_comments(anime["id"], episode)

    # Convert datetime objects to strings for JSON serialization
    for c in comments:
        if 'created_at' in c and c['created_at']:
            c['created_at'] = c['created_at'].isoformat()

    return jsonify(comments)

@comments_bp.route("/api/comments", methods=["POST"])
def post_comment():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    mal_id = data.get("mal_id")
    episode = data.get("episode")
    content = data.get("content")
    is_spoiler = data.get("is_spoiler", False)

    if not mal_id or not episode or not content:
        return jsonify({"error": "Missing fields"}), 400

    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    success = db.add_comment(session["user_id"], anime["id"], episode, content, is_spoiler)
    if success:
        return jsonify({"success": True})

    return jsonify({"error": "Failed to post comment"}), 500
