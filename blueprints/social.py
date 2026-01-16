from flask import Blueprint, request, jsonify, session
import db
from datetime import datetime

social_bp = Blueprint('social', __name__)

@social_bp.route("/api/comments/<int:mal_id>/<int:ep>")
def get_comments(mal_id, ep):
    """Bölüm yorumlarını getir."""
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify([])

    comments = db.get_comments_by_episode(anime['id'], ep)

    # JSON serileştirme için datetime'ları string'e çevir
    for c in comments:
        if isinstance(c['created_at'], datetime):
            c['created_at'] = c['created_at'].isoformat()

    return jsonify(comments)

@social_bp.route("/api/comments", methods=["POST"])
def post_comment():
    """Yeni yorum yap."""
    if "user_id" not in session:
        return jsonify({"error": "Lütfen önce giriş yapın"}), 401

    data = request.get_json()
    mal_id = data.get("mal_id")
    ep = data.get("episode")
    content = data.get("content")
    is_spoiler = data.get("is_spoiler", False)

    if not content or len(content.strip()) < 2:
        return jsonify({"error": "Yorum çok kısa"}), 400

    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime bulunamadı"}), 404

    comment_id = db.add_comment(
        user_id=session["user_id"],
        anime_id=anime['id'],
        episode_number=ep,
        content=content,
        is_spoiler=is_spoiler
    )

    if comment_id:
        return jsonify({"success": True, "comment_id": comment_id})
    else:
        return jsonify({"error": "Yorum eklenemedi"}), 500

@social_bp.route("/api/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    """Yorumu sil."""
    if "user_id" not in session:
        return jsonify({"error": "Yetkisiz işlem"}), 401

    success = db.delete_comment(comment_id, session["user_id"])
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Yorum silinemedi veya yetkiniz yok"}), 403
