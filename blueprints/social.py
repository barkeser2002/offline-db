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
    parent_id = data.get("parent_id")

    if not mal_id or not episode or not content:
        return jsonify({"error": "Missing fields"}), 400

    # Get internal anime ID
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    # Convert to dict if it's a Row object
    anime = dict(anime)

    comment_id = db.add_comment(
        session["user_id"],
        int(anime["id"]),
        int(episode),
        content,
        bool(is_spoiler),
        parent_id
    )

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

    # Use db.get_comments for threaded structure
    comments = db.get_comments(anime["id"], episode)

    # Format datetime for JSON
    comments = db.serialize_for_json(comments)

    return jsonify(comments)

@social_bp.route("/api/social/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    success = db.delete_comment(comment_id, session["user_id"])

    if success:
        return jsonify({"success": True})

    return jsonify({"error": "Failed to delete comment or unauthorized"}), 403

@social_bp.route("/api/social/trending", methods=["GET"])
def get_trending():
    limit = request.args.get("limit", 10, type=int)
    days = request.args.get("days", 7, type=int)

    trending = db.get_trending_anime(limit, days)

    # Format for JSON serialization
    trending = db.serialize_for_json(trending)

    return jsonify(trending)

@social_bp.route("/api/social/recommendations", methods=["GET"])
def get_recommendations():
    if "user_id" not in session:
        return jsonify([])

    limit = request.args.get("limit", 5, type=int)
    recommendations = db.get_personalized_recommendations(session["user_id"], limit)

    # Format for JSON serialization
    recommendations = db.serialize_for_json(recommendations)

    return jsonify(recommendations)
