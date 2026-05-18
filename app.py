from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import sqlite3
import re
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'is211_blog_secret_key_2024'

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

DATABASE = 'blog.db'

# ─────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table (extra credit: multiple users)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Categories table (extra credit)
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Posts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            category_id INTEGER,
            published INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            FOREIGN KEY (author_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')

    # Seed default users
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'password'))
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('jane', 'password'))
    except sqlite3.IntegrityError:
        pass  # Users already exist

    conn.commit()
    conn.close()

# ─────────────────────────────────────────
# Auth decorator
# ─────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access that page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────
# Slug helper
# ─────────────────────────────────────────

def slugify(title):
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug.strip('-')
    # Ensure uniqueness
    conn = get_db()
    base = slug
    i = 1
    while conn.execute('SELECT id FROM posts WHERE slug = ?', (slug,)).fetchone():
        slug = f'{base}-{i}'
        i += 1
    conn.close()
    return slug

# ─────────────────────────────────────────
# Public routes
# ─────────────────────────────────────────

@app.route('/')
def index():
    conn = get_db()
    posts = conn.execute('''
        SELECT posts.*, users.username AS author_name, categories.name AS category_name
        FROM posts
        JOIN users ON posts.author_id = users.id
        LEFT JOIN categories ON posts.category_id = categories.id
        WHERE posts.published = 1
        ORDER BY posts.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/post/<slug>')
def view_post(slug):
    conn = get_db()
    post = conn.execute('''
        SELECT posts.*, users.username AS author_name, categories.name AS category_name
        FROM posts
        JOIN users ON posts.author_id = users.id
        LEFT JOIN categories ON posts.category_id = categories.id
        WHERE posts.slug = ? AND posts.published = 1
    ''', (slug,)).fetchone()
    conn.close()
    if not post:
        abort(404)
    return render_template('post.html', post=post)

@app.route('/category/<int:cat_id>')
def category_posts(cat_id):
    conn = get_db()
    category = conn.execute('SELECT * FROM categories WHERE id = ?', (cat_id,)).fetchone()
    if not category:
        abort(404)
    posts = conn.execute('''
        SELECT posts.*, users.username AS author_name, categories.name AS category_name
        FROM posts
        JOIN users ON posts.author_id = users.id
        LEFT JOIN categories ON posts.category_id = categories.id
        WHERE posts.category_id = ? AND posts.published = 1
        ORDER BY posts.created_at DESC
    ''', (cat_id,)).fetchall()
    conn.close()
    return render_template('category.html', posts=posts, category=category)

# ─────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                            (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Welcome back, ' + user['username'] + '!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# ─────────────────────────────────────────
# Dashboard (protected)
# ─────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    posts = conn.execute('''
        SELECT posts.*, categories.name AS category_name
        FROM posts
        LEFT JOIN categories ON posts.category_id = categories.id
        WHERE posts.author_id = ?
        ORDER BY posts.created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', posts=posts)

# ─────────────────────────────────────────
# Post CRUD
# ─────────────────────────────────────────

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    conn = get_db()
    categories = conn.execute('SELECT * FROM categories WHERE user_id = ?',
                              (session['user_id'],)).fetchall()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        cat_id = request.form.get('category_id') or None
        if not title or not content:
            flash('Title and content are required.', 'error')
        else:
            slug = slugify(title)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute('''
                INSERT INTO posts (title, content, author_id, category_id, published, created_at, slug)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            ''', (title, content, session['user_id'], cat_id, now, slug))
            conn.commit()
            conn.close()
            flash('Post published!', 'success')
            return redirect(url_for('dashboard'))
    conn.close()
    return render_template('post_form.html', post=None, categories=categories)

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ? AND author_id = ?',
                        (post_id, session['user_id'])).fetchone()
    if not post:
        abort(403)
    categories = conn.execute('SELECT * FROM categories WHERE user_id = ?',
                              (session['user_id'],)).fetchall()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        cat_id = request.form.get('category_id') or None
        if not title or not content:
            flash('Title and content are required.', 'error')
        else:
            conn.execute('''
                UPDATE posts SET title=?, content=?, category_id=? WHERE id=?
            ''', (title, content, cat_id, post_id))
            conn.commit()
            conn.close()
            flash('Post updated!', 'success')
            return redirect(url_for('dashboard'))
    conn.close()
    return render_template('post_form.html', post=post, categories=categories)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ? AND author_id = ?',
                        (post_id, session['user_id'])).fetchone()
    if not post:
        abort(403)
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    flash('Post deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/post/<int:post_id>/toggle', methods=['POST'])
@login_required
def toggle_publish(post_id):
    conn = get_db()
    post = conn.execute('SELECT * FROM posts WHERE id = ? AND author_id = ?',
                        (post_id, session['user_id'])).fetchone()
    if not post:
        abort(403)
    new_status = 0 if post['published'] else 1
    conn.execute('UPDATE posts SET published = ? WHERE id = ?', (new_status, post_id))
    conn.commit()
    conn.close()
    status_word = 'published' if new_status else 'unpublished'
    flash(f'Post {status_word}.', 'success')
    return redirect(url_for('dashboard'))

# ─────────────────────────────────────────
# Categories (extra credit)
# ─────────────────────────────────────────

@app.route('/categories')
@login_required
def manage_categories():
    conn = get_db()
    categories = conn.execute('SELECT * FROM categories WHERE user_id = ?',
                              (session['user_id'],)).fetchall()
    conn.close()
    return render_template('categories.html', categories=categories)

@app.route('/categories/new', methods=['POST'])
@login_required
def new_category():
    name = request.form.get('name', '').strip()
    if name:
        try:
            conn = get_db()
            conn.execute('INSERT INTO categories (name, user_id) VALUES (?, ?)',
                         (name, session['user_id']))
            conn.commit()
            conn.close()
            flash(f'Category "{name}" created.', 'success')
        except sqlite3.IntegrityError:
            flash('A category with that name already exists.', 'error')
    return redirect(url_for('manage_categories'))

@app.route('/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
def delete_category(cat_id):
    conn = get_db()
    conn.execute('UPDATE posts SET category_id = NULL WHERE category_id = ?', (cat_id,))
    conn.execute('DELETE FROM categories WHERE id = ? AND user_id = ?',
                 (cat_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Category deleted.', 'success')
    return redirect(url_for('manage_categories'))

# ─────────────────────────────────────────
# Error handlers
# ─────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='Page not found.'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, message='You are not allowed to do that.'), 403

# ─────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
