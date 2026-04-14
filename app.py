from flask import Flask, render_template_string, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("todo.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            title TEXT,
            done INTEGER
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- UI ----------------
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>To-Do App</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
        body { background: #f4f6f8; }
        .card { border-radius: 15px; }
        .done { text-decoration: line-through; color: gray; }
    </style>
</head>

<body>

<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">

            <div class="card shadow p-4">

                <h3 class="text-center mb-4">📝 To-Do App</h3>

                <form method="POST" action="/add" class="d-flex gap-2 mb-3">
                    <input name="task" class="form-control" placeholder="Enter task">
                    <button class="btn btn-success">Add</button>
                </form>

                <ul class="list-group">

                {% for task in tasks %}
                    <li class="list-group-item d-flex justify-content-between align-items-center">

                        <span class="{{ 'done' if task['done'] else '' }}">
                            {{ task['title'] }}
                        </span>

                        <div>
                            <a class="btn btn-sm btn-success" href="/done/{{ loop.index0 }}">✔</a>
                            <a class="btn btn-sm btn-danger" href="/delete/{{ loop.index0 }}">✖</a>
                        </div>

                    </li>
                {% endfor %}

                </ul>

                <hr>

                <a href="/logout" class="btn btn-secondary w-100">Logout</a>

            </div>

        </div>
    </div>
</div>

</body>
</html>
"""

# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("todo.db")
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, password))
            conn.commit()
        except:
            return "User already exists"

        conn.close()
        return redirect("/login")

    return """
    <h2>Register</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button>Register</button>
    </form>
    """

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("todo.db")
        c = conn.cursor()

        c.execute("SELECT password FROM users WHERE username=?", (username,))
        user = c.fetchone()

        conn.close()

        if user and check_password_hash(user[0], password):
            session["user"] = username
            return redirect("/tasks")

        return "Invalid login"

    return """
    <h2>Login</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button>Login</button>
    </form>
    """

# ---------------- TASKS ----------------
@app.route("/tasks")
def tasks():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("todo.db")
    c = conn.cursor()

    c.execute("SELECT title, done FROM tasks WHERE user=?", (session["user"],))
    tasks = [{"title": t[0], "done": t[1]} for t in c.fetchall()]

    conn.close()

    return render_template_string(HTML, tasks=tasks)

# ---------------- ADD TASK ----------------
@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("todo.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO tasks (user, title, done) VALUES (?, ?, ?)",
        (session["user"], request.form["task"], 0)
    )

    conn.commit()
    conn.close()

    return redirect("/tasks")

# ---------------- DONE TASK ----------------
@app.route("/done/<int:index>")
def done(index):
    conn = sqlite3.connect("todo.db")
    c = conn.cursor()

    c.execute("SELECT id FROM tasks WHERE user=?", (session["user"],))
    ids = [row[0] for row in c.fetchall()]

    if index < len(ids):
        c.execute("UPDATE tasks SET done=1 WHERE id=?", (ids[index],))

    conn.commit()
    conn.close()

    return redirect("/tasks")

# ---------------- DELETE TASK ----------------
@app.route("/delete/<int:index>")
def delete(index):
    conn = sqlite3.connect("todo.db")
    c = conn.cursor()

    c.execute("SELECT id FROM tasks WHERE user=?", (session["user"],))
    ids = [row[0] for row in c.fetchall()]

    if index < len(ids):
        c.execute("DELETE FROM tasks WHERE id=?", (ids[index],))

    conn.commit()
    conn.close()

    return redirect("/tasks")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=10000)