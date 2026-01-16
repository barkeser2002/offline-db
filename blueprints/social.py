from flask import Blueprint, request, jsonify, session
import db
from datetime import datetime

social_bp = Blueprint('social', __name__)

@social_bp.route("/api/comments", methods=["GET"])
def get_comments():
    mal_id = request.args.get("mal_id", type=int)
    episode = request.args.get("episode", type=int)

    if not mal_id or not episode:
        return jsonify({"error": "mal_id and episode are required"}), 400

    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    comments = db.get_episode_comments(anime["id"], episode)

    # Format datetime to string for JSON serialization
    for comment in comments:
        if isinstance(comment["created_at"], datetime):
            comment["created_at"] = comment["created_at"].isoformat()

    return jsonify(comments)

@social_bp.route("/api/comments", methods=["POST"])
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

    comment_id = db.add_comment(
        user_id=session["user_id"],
        anime_id=anime["id"],
        episode_number=episode,
        content=content,
        is_spoiler=is_spoiler
    )

    if comment_id:
        return jsonify({
            "success": True,
            "comment_id": comment_id,
            "username": session["username"],
            "created_at": datetime.now().isoformat()
        })

    return jsonify({"error": "Failed to post comment"}), 500

@social_bp.route("/api/trending", methods=["GET"])
def get_trending():
    limit = request.args.get("limit", 10, type=int)
    days = request.args.get("days", 7, type=int)

    trending = db.get_trending_anime(limit, days)

    # Format for JSON serialization
    from decimal import Decimal
    from datetime import date, datetime

    for item in trending:
        for key, value in item.items():
            if isinstance(value, Decimal):
                item[key] = float(value)
            elif isinstance(value, (datetime, date)):
                item[key] = value.isoformat()

    return jsonify(trending)
