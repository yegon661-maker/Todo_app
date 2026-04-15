from flask import Flask, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# -------- DATABASE --------
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
        username TEXT,
        task TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------- REGISTER --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("todo.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if c.fetchone():
            return "User already exists"

        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return """
    <h2>Register</h2>
    <form method="POST">
        <input name="username" placeholder="Username" required><br><br>
        <input name="password" type="password" placeholder="Password" required><br><br>
        <button>Register</button>
    </form>
    <a href="/login">Login</a>
    """

# -------- LOGIN --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("todo.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
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
    <a href="/register">Register</a>
    """

# -------- TASKS --------
@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    conn = sqlite3.connect("todo.db")
    c = conn.cursor()

    # EDIT SETUP
    edit_id = request.args.get("edit")
    edit_task = None

    if edit_id:
        c.execute("SELECT task FROM tasks WHERE id=?", (edit_id,))
        edit_task = c.fetchone()

    # ADD / UPDATE
    if request.method == "POST":
        task = request.form["task"]

        if "update_id" in request.form:
            task_id = request.form["update_id"]
            c.execute("UPDATE tasks SET task=? WHERE id=?", (task, task_id))
        else:
            c.execute("INSERT INTO tasks (username, task) VALUES (?, ?)", (user, task))

        conn.commit()
        return redirect("/tasks")

    # DELETE
    delete_id = request.args.get("delete")
    if delete_id:
        c.execute("DELETE FROM tasks WHERE id=?", (delete_id,))
        conn.commit()
        return redirect("/tasks")

    # FETCH
    if user == "admin":
        c.execute("SELECT id, username, task FROM tasks")
        tasks = c.fetchall()
    else:
        c.execute("SELECT id, task FROM tasks WHERE username=?", (user,))
        tasks = c.fetchall()

    conn.close()

    # BUILD LIST
    task_list = ""
    for t in tasks:
        if user == "admin":
            task_list += f"<li><b>{t[1]}</b>: {t[2]} <a href='?edit={t[0]}'>✏️</a> <a href='?delete={t[0]}'>❌</a></li>"
        else:
            task_list += f"<li>{t[1]} <a href='?edit={t[0]}'>✏️</a> <a href='?delete={t[0]}'>❌</a></li>"

    admin_link = ""
    if user == "admin":
        admin_link = '<a href="/admin">Admin Panel</a>'

    return f"""
    <html>
    <head>
    <style>
    body {{
        margin: 0;
        font-family: Arial;
        background: linear-gradient(135deg, #74ebd5, #ACB6E5);
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
    }}

    .card {{
        background: white;
        padding: 25px;
        width: 420px;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        text-align: center;
    }}

    input {{
        padding: 10px;
        width: 70%;
        border-radius: 8px;
        border: 1px solid #ccc;
    }}

    button {{
        padding: 10px;
        background: green;
        color: white;
        border: none;
        border-radius: 8px;
    }}

    ul {{
        text-align: left;
        padding: 0;
    }}

    li {{
        background: #f4f4f4;
        margin: 8px 0;
        padding: 10px;
        border-radius: 8px;
    }}
    </style>
    </head>

    <body>
    <div class="card">

    <h2>Welcome {user}</h2>

    {admin_link}

    <form method="POST">
        <input name="task" value="{edit_task[0] if edit_task else ''}" placeholder="Enter task" required>
        {"<input type='hidden' name='update_id' value='" + str(edit_id) + "'>" if edit_task else ""}
        <button>{'Update Task' if edit_task else 'Add Task'}</button>
    </form>

    <h3>Your Tasks</h3>
    <ul>
        {task_list}
    </ul>

    <br>
    <a href="/logout">Logout</a>

    </div>
    </body>
    </html>
    """

# -------- ADMIN --------
@app.route("/admin")
def admin():
    if session.get("user") != "admin":
        return redirect("/login")

    conn = sqlite3.connect("todo.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    users = c.fetchall()
    conn.close()

    user_list = "".join([f"<li>{u[0]}</li>" for u in users])

    return f"""
    <h2>Admin Panel</h2>
    <ul>{user_list}</ul>
    <a href="/tasks">Back</a>
    """

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)