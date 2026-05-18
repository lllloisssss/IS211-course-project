# The Daily Write — IS211 Course Project

A full-featured blogging web application built with Python, Flask, and SQLite.

---

## How to Run

1. **Install dependencies:**
   ```bash
   pip install flask
   ```

2. **Start the application:**
   ```bash
   python app.py
   ```

3. **Open your browser** and navigate to:
   ```
   http://127.0.0.1:5000
   ```

That's it. The database (`blog.db`) is created automatically on first run, along with two demo user accounts.

---

## Demo Accounts

| Username | Password |
|----------|----------|
| admin    | password |
| jane     | password |

---

## Application Overview

**The Daily Write** is a multi-user blogging platform. Visitors can read published posts on the homepage, sorted newest-first. Authenticated authors can log in at `/login` to reach their personal dashboard, where they can create, edit, delete, publish, and unpublish posts. Each post also belongs to a user-defined category.

### Routes

| URL                          | Access     | Description                                  |
|------------------------------|------------|----------------------------------------------|
| `/`                          | Public     | Homepage — all published posts, newest first |
| `/post/<slug>`               | Public     | Single post view with permalink              |
| `/category/<id>`             | Public     | All posts in a given category                |
| `/login`                     | Public     | Login form                                   |
| `/logout`                    | Auth       | Log out and clear session                    |
| `/dashboard`                 | Auth       | Manage your posts                            |
| `/post/new`                  | Auth       | Create a new post                            |
| `/post/<id>/edit`            | Auth       | Edit an existing post                        |
| `/post/<id>/delete`          | Auth (POST)| Delete a post                                |
| `/post/<id>/toggle`          | Auth (POST)| Publish / unpublish a post                   |
| `/categories`                | Auth       | Manage categories                            |
| `/categories/new`            | Auth (POST)| Create a category                            |
| `/categories/<id>/delete`    | Auth (POST)| Delete a category                            |

---

## Database Model

The application uses three tables stored in a single SQLite file (`blog.db`):

### `users`
Stores registered accounts. Supports multiple independent authors.

| Column   | Type    | Notes                        |
|----------|---------|------------------------------|
| id       | INTEGER | Primary key, auto-increment  |
| username | TEXT    | Unique login name            |
| password | TEXT    | Plaintext (per spec)         |

### `categories`
User-defined categories for organizing posts.

| Column  | Type    | Notes                              |
|---------|---------|------------------------------------|
| id      | INTEGER | Primary key, auto-increment        |
| name    | TEXT    | Unique category label              |
| user_id | INTEGER | Foreign key → users.id (owner)    |

### `posts`
The core content table. Each post belongs to one author and optionally one category.

| Column      | Type    | Notes                                        |
|-------------|---------|----------------------------------------------|
| id          | INTEGER | Primary key, auto-increment                  |
| title       | TEXT    | Post headline                                |
| content     | TEXT    | Full post body (HTML supported)              |
| author_id   | INTEGER | Foreign key → users.id                      |
| category_id | INTEGER | Foreign key → categories.id (nullable)      |
| published   | INTEGER | 1 = published, 0 = draft/unpublished         |
| created_at  | TEXT    | ISO datetime string (YYYY-MM-DD HH:MM:SS)    |
| slug        | TEXT    | Unique URL-safe identifier (auto-generated)  |

---

## Extra Credit Features Implemented

1. **Multiple users** — `users` table with credentials; both `admin` and `jane` can log in and manage their own posts independently.
2. **Permalinks** — Each post gets a unique URL slug auto-generated from its title (e.g. `/post/my-first-post`). The permalink is displayed on the post detail page.
3. **Unpublish / Re-publish** — The dashboard includes a toggle button that sets `published = 0` without deleting the post. Unpublished posts are hidden from the public homepage and can be re-published at any time.
4. **Categories** — Authors can create their own category list, assign categories to posts, and visitors can browse all posts within a given category via a dedicated URL.

---

## Technology Stack

- **Python 3** with **Flask** — routing, templating, session management
- **SQLite 3** — lightweight embedded database (no server required)
- **Jinja2** — HTML templating (included with Flask)
- **Google Fonts** — Playfair Display + DM Sans + DM Mono (editorial aesthetic)
- No external JavaScript frameworks — pure HTML/CSS/JS
