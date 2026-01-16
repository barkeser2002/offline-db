from flask import Blueprint, request, jsonify, session
import db

social_bp = Blueprint('social', __name__)

@social_bp.route("/api/social/comments", methods=["POST"])
def add_comment():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    mal_id = data.get("mal_id")
    episode = data.get("episode")
    content = data.get("content")
    is_spoiler = data.get("is_spoiler", False)

    if not mal_id or not episode or not content:
        return jsonify({"error": "Missing fields"}), 400

    # Get internal anime ID
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    comment_id = db.add_comment(session["user_id"], anime["id"], episode, content, is_spoiler)

    if comment_id:
        return jsonify({
            "success": True,
            "comment_id": comment_id,
            "username": session["username"]
        })

    return jsonify({"error": "Failed to add comment"}), 500

@social_bp.route("/api/social/comments/<int:mal_id>/<int:episode>", methods=["GET"])
def get_comments(mal_id, episode):
    # Get internal anime ID
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    comments = db.get_episode_comments(anime["id"], episode)

    # Format datetime for JSON
    for c in comments:
        if c.get("created_at"):
            c["created_at"] = c["created_at"].isoformat()

    return jsonify(comments)

@social_bp.route("/api/social/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    success = db.delete_comment(comment_id, session["user_id"])

    if success:
        return jsonify({"success": True})

    return jsonify({"error": "Failed to delete comment or unauthorized"}), 403
