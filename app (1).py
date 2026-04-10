from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yachay-secreto-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'webm'}

os.makedirs('uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)

POSTS_FILE = 'data/posts.json'

def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_posts(posts):
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = load_posts()
    posts.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(posts)

@app.route('/api/posts', methods=['POST'])
def create_post():
    posts = load_posts()
    
    content = request.form.get('content', '').strip()
    author = request.form.get('author', 'Anónimo').strip() or 'Anónimo'
    category = request.form.get('category', 'general')
    
    if not content:
        return jsonify({'error': 'El chisme no puede estar vacío'}), 400

    media_files = []
    
    if 'media' in request.files:
        files = request.files.getlist('media')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                media_type = 'video' if ext in {'mp4', 'mov', 'webm'} else 'image'
                media_files.append({'url': f'/uploads/{filename}', 'type': media_type})

    post = {
        'id': str(uuid.uuid4()),
        'content': content,
        'author': author,
        'category': category,
        'media': media_files,
        'timestamp': datetime.now().isoformat(),
        'likes': 0,
        'comments': [],
        'reactions': {'🔥': 0, '😱': 0, '💀': 0, '🤣': 0, '👀': 0}
    }
    
    posts.append(post)
    save_posts(posts)
    
    return jsonify(post), 201

@app.route('/api/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    posts = load_posts()
    for post in posts:
        if post['id'] == post_id:
            post['likes'] += 1
            save_posts(posts)
            return jsonify({'likes': post['likes']})
    return jsonify({'error': 'Post no encontrado'}), 404

@app.route('/api/posts/<post_id>/react', methods=['POST'])
def react_post(post_id):
    data = request.get_json()
    emoji = data.get('emoji')
    posts = load_posts()
    for post in posts:
        if post['id'] == post_id:
            if emoji in post['reactions']:
                post['reactions'][emoji] += 1
                save_posts(posts)
                return jsonify({'reactions': post['reactions']})
    return jsonify({'error': 'Post no encontrado'}), 404

@app.route('/api/posts/<post_id>/comment', methods=['POST'])
def add_comment(post_id):
    data = request.get_json()
    comment_text = data.get('text', '').strip()
    author = data.get('author', 'Anónimo').strip() or 'Anónimo'
    
    if not comment_text:
        return jsonify({'error': 'Comentario vacío'}), 400
    
    posts = load_posts()
    for post in posts:
        if post['id'] == post_id:
            comment = {
                'id': str(uuid.uuid4()),
                'text': comment_text,
                'author': author,
                'timestamp': datetime.now().isoformat()
            }
            post['comments'].append(comment)
            save_posts(posts)
            return jsonify(comment), 201
    return jsonify({'error': 'Post no encontrado'}), 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
