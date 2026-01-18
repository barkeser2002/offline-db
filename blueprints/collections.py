from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import db

collections_bp = Blueprint('collections', __name__)

@collections_bp.route("/collections")
def collections_list():
    """User's own collections or all public collections if not logged in."""
    if "user_id" in session:
        user_collections = db.get_user_collections(session["user_id"])
        return render_template("collections.html", collections=user_collections, is_own=True)

    # Show public collections? (For now just redirect to login if not logged in)
    return redirect(url_for('ui.login'))

@collections_bp.route("/collection/<int:collection_id>")
def collection_view(collection_id):
    """View a specific collection."""
    collection = db.get_collection_details(collection_id)
    if not collection:
        return "Collection not found", 404

    # Check visibility
    if not collection["is_public"] and ( "user_id" not in session or session["user_id"] != collection["user_id"] ):
        return "This collection is private", 403

    is_owner = "user_id" in session and session["user_id"] == collection["user_id"]
    return render_template("collection_view.html", collection=collection, is_owner=is_owner)

# API Endpoints

@collections_bp.route("/api/collections", methods=["GET", "POST"])
def api_collections():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == "POST":
        data = request.get_json()
        name = data.get("name")
        description = data.get("description")
        is_public = data.get("is_public", True)

        if not name:
            return jsonify({"error": "Name is required"}), 400

        col_id = db.create_collection(session["user_id"], name, description, is_public)
        if col_id:
            return jsonify({"success": True, "collection_id": col_id})
        return jsonify({"error": "Failed to create collection"}), 500

    else:
        # GET - list my collections
        user_collections = db.get_user_collections(session["user_id"])
        return jsonify({"success": True, "collections": db.serialize_for_json(user_collections)})

@collections_bp.route("/api/collections/<int:collection_id>", methods=["GET", "PUT", "DELETE"])
def api_collection_detail(collection_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # Check ownership for PUT/DELETE
    collection = db.get_collection_details(collection_id)
    if not collection:
        return jsonify({"error": "Not found"}), 404

    if request.method == "DELETE":
        if collection["user_id"] != session["user_id"]:
            return jsonify({"error": "Forbidden"}), 403

        success = db.delete_collection(collection_id, session["user_id"])
        return jsonify({"success": success})

    elif request.method == "PUT":
        if collection["user_id"] != session["user_id"]:
            return jsonify({"error": "Forbidden"}), 403

        data = request.get_json()
        name = data.get("name", collection["name"])
        description = data.get("description", collection["description"])
        is_public = data.get("is_public", collection["is_public"])

        success = db.update_collection(collection_id, session["user_id"], name, description, is_public)
        return jsonify({"success": success})

    else:
        # GET
        if not collection["is_public"] and collection["user_id"] != session["user_id"]:
            return jsonify({"error": "Private collection"}), 403
        return jsonify({"success": True, "collection": db.serialize_for_json(collection)})

@collections_bp.route("/api/collections/<int:collection_id>/items", methods=["POST"])
def api_collection_add_item(collection_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    collection = db.get_collection_details(collection_id)
    if not collection or collection["user_id"] != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    mal_id = data.get("mal_id")
    if not mal_id:
        return jsonify({"error": "mal_id required"}), 400

    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    success = db.add_to_collection(collection_id, anime["id"])
    return jsonify({"success": success})

@collections_bp.route("/api/collections/<int:collection_id>/items/<int:mal_id>", methods=["DELETE"])
def api_collection_remove_item(collection_id, mal_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    collection = db.get_collection_details(collection_id)
    if not collection or collection["user_id"] != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403

    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    success = db.remove_from_collection(collection_id, anime["id"])
    return jsonify({"success": success})
