from flask import Blueprint, request, jsonify, session
import db

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route("/api/reviews", methods=["POST"])
def add_review():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    mal_id = data.get("mal_id")
    score = data.get("score")
    title = data.get("title")
    content = data.get("content")
    is_spoiler = data.get("is_spoiler", False)

    if not mal_id or not score or not content:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        score = int(score)
        if not (1 <= score <= 10):
            return jsonify({"error": "Score must be between 1 and 10"}), 400
    except ValueError:
        return jsonify({"error": "Invalid score format"}), 400

    # Get internal anime ID
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    success = db.add_review(
        session["user_id"],
        anime["id"],
        score,
        title,
        content,
        is_spoiler
    )

    if success:
        # Log activity
        db.add_user_activity(session["user_id"], "review", anime_id=anime["id"], message=f"Reviewed {anime['title']}")
        return jsonify({"success": True, "message": "Review submitted successfully"})

    return jsonify({"error": "Failed to submit review"}), 500

@reviews_bp.route("/api/reviews/<int:mal_id>", methods=["GET"])
def get_reviews(mal_id):
    # Get internal anime ID
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    current_user_id = session.get("user_id")
    reviews = db.get_reviews_by_anime(anime["id"], current_user_id)

    # Serialize for JSON
    serialized_reviews = db.serialize_for_json(reviews)

    return jsonify(serialized_reviews)

@reviews_bp.route("/api/reviews/<int:review_id>/vote", methods=["POST"])
def vote_review(review_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    vote_type = data.get("vote") # 1 or -1

    if vote_type not in [1, -1]:
        return jsonify({"error": "Invalid vote type"}), 400

    success = db.vote_review(review_id, session["user_id"], vote_type)

    if success:
        return jsonify({"success": True})

    return jsonify({"error": "Failed to record vote"}), 500

@reviews_bp.route("/api/reviews/<int:review_id>", methods=["DELETE"])
def delete_review(review_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    success = db.delete_review(review_id, session["user_id"])

    if success:
        return jsonify({"success": True})

    return jsonify({"error": "Failed to delete review or unauthorized"}), 403
