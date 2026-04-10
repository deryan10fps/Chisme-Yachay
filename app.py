from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader
import uuid
from datetime import datetime
import os

app = Flask(__name__)

# ================= DB =================
uri = os.getenv("DATABASE_URL")

# Fix importante para Render PostgreSQL
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri or "sqlite:///db.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= CLOUDINARY =================
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# ================= MODELOS =================
class Post(db.Model):
    id = db.Column(db.String, primary_key=True)
    author = db.Column(db.String(100))
    content = db.Column(db.Text)
    category = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)

class Comment(db.Model):
    id = db.Column(db.String, primary_key=True)
    post_id = db.Column(db.String)
    author = db.Column(db.String(100))
    text = db.Column(db.Text)

# ================= RUTAS =================

@app.route('/')
def index():
    return render_template('index.html')

# 🔥 OBTENER POSTS
@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    result = []

    for p in posts:
        comments = Comment.query.filter_by(post_id=p.id).all()

        result.append({
            "id": p.id,
            "author": p.author,
            "content": p.content,
            "category": p.category,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            "likes": p.likes,
            "comments": [{"author": c.author, "text": c.text} for c in comments],
            "reactions": {"🔥": 0, "😱": 0, "😂": 0},
            "media": []
        })

    return jsonify(result)

# 🚀 CREAR POST
@app.route('/api/posts', methods=['POST'])
def create_post():
    content = request.form.get('content')
    author = request.form.get('author', 'Anónimo')
    category = request.form.get('category', 'general')

    media_urls = []

    if 'media' in request.files:
        files = request.files.getlist('media')
        for file in files:
            if file.filename:
                result = cloudinary.uploader.upload(file)
                media_urls.append(result["secure_url"])

    new_post = Post(
        id=str(uuid.uuid4()),
        author=author,
        content=content,
        category=category,
        timestamp=datetime.utcnow(),
        likes=0
    )

    db.session.add(new_post)
    db.session.commit()

    return jsonify({
        "id": new_post.id,
        "author": new_post.author,
        "content": new_post.content,
        "category": new_post.category,
        "timestamp": new_post.timestamp.isoformat(),
        "likes": new_post.likes,
        "comments": [],
        "reactions": {"🔥": 0, "😱": 0, "😂": 0},
        "media": [{"url": url, "type": "image"} for url in media_urls]
    })

# 👍 LIKE
@app.route('/api/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    post = Post.query.get(post_id)
    if post:
        post.likes += 1
        db.session.commit()
        return jsonify({"likes": post.likes})
    return jsonify({"error": "No encontrado"}), 404

# 💬 COMENTARIOS
@app.route('/api/posts/<post_id>/comment', methods=['POST'])
def add_comment(post_id):
    data = request.get_json()

    comment = Comment(
        id=str(uuid.uuid4()),
        post_id=post_id,
        author=data.get('author', 'Anónimo'),
        text=data.get('text')
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "author": comment.author,
        "text": comment.text
    })

# ================= INIT =================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
