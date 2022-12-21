from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import time
import datetime


app = Flask(__name__)

# conn = sqlite3.connect("Chirper.db")
# c = conn.cursor()
# c.execute("CREATE TABLE chirps (chirp_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, text_content TEXT, media_content TEXT, date_num NUMERIC NOT NULL, date_date TEXT NOT NULL)")
# c.execute("CREATE TABLE followers (user TEXT NOT NULL, follower TEXT NOT NULL)")
# c.execute("CREATE TABLE replies (chirp_id INTEGER NOT NULL, username TEXT NOT NULL, text_content TEXT NOT NULL, media_content TEXT NOT NULL, date_num NUMERIC NOT NULL, date_date TEXT NOT NULL)")
# c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, password_hash TEXT NOT NULL, joined_date TEXT NOT NULL, following INTEGER, followers INTEGER, bio TEXT)")

username = ''

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        global username
        username = request.form.get("username")
        password = request.form.get("password")
        conn = sqlite3.connect("Chirper.db")
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        sql_return = c.fetchall()
        c.close()
        if not sql_return:
            return redirect("/")
        sql_password_hash = sql_return[0][0]
        if check_password_hash(sql_password_hash, password):
            return redirect("/home")
        else:
            return redirect("/")
    return render_template("login.html")



@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        text_content = request.form.get("chirp")
        media_content = request.form.get("media")
        date_num = time.time()
        date_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("Chirper.db")
        c = conn.cursor()
        print("here")
        print(username)
        c.execute("INSERT INTO chirps (username, text_content, media_content, date_num, date_date) VALUES (?, ?, ?, ?, ?)", (username, text_content, media_content, date_num, date_date))
        conn.commit()
        c.close()
        print("here2")
        return redirect("/home")
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    print(username)
    c.execute("SELECT * FROM chirps WHERE username IN (SELECT user FROM followers WHERE follower = ?) UNION SELECT * FROM chirps WHERE username = ? ORDER BY date_num DESC", (username, username))
    chirps = c.fetchall()
    print(chirps)
    c.close()
    return render_template("index.html", chirps=chirps)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if len(username) == 0 or len(password) == 0:
            redirect("register.html")

        conn = sqlite3.connect("Chirper.db")
        c = conn.cursor()
        #check if username already used
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_list = c.fetchall()
        print(user_list)
        if not user_list:
            password_hash = generate_password_hash(password)
            date = datetime.datetime.now().strftime("%B %Y")
            c.execute("INSERT INTO users (username, password_hash, joined_date, following, followers) VALUES (?, ?, ?, ?, ?)", (username, password_hash, date, 0, 0))
            conn.commit()
            return redirect("/")
    return render_template("register.html")



@app.route("/reply/<int:chirp_id>", methods=["GET", "POST"])
def reply(chirp_id):
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    if request.method == "POST":
        text_content = request.form.get("reply")
        media_content = request.form.get("media")
        date_num = time.time()
        date_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("here1")
        c.execute("INSERT INTO replies (chirp_id, username, text_content, media_content, date_num, date_date) VALUES (?, ?, ?, ?, ?, ?)", (chirp_id, username, text_content, media_content, date_num, date_date))
        print("here2")
        conn.commit()
        return redirect(url_for("reply", chirp_id=chirp_id))

    c.execute("SELECT * FROM chirps WHERE chirp_id = ?", (chirp_id,))
    chirp = c.fetchall()[0]
    c.execute("SELECT * from replies WHERE chirp_id = ? ORDER BY date_num ASC", (chirp_id,))
    replies = c.fetchall()
    return render_template("reply.html", chirp=chirp, replies=replies)

@app.route("/account/<to_follow>")
def account(to_follow):
    print(to_follow)
    lower_to_follow = to_follow.lower()
    print(lower_to_follow)
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT * FROM chirps WHERE LOWER(username) = ? ORDER BY date_num ASC", (lower_to_follow,))
    chirps = c.fetchall()
    print(chirps)
    return render_template("account.html", to_follow=to_follow, chirps=chirps)



@app.route("/explore")
def explore():
    return render_template("explore.html")

@app.route("/notifications")
def notifications():
    return render_template("notifications.html")

@app.route("/messages")
def messages():
    return render_template("messages.html")

@app.route("/bookmarks")
def bookmarks():
    return render_template("bookmarks.html")

@app.route("/blue")
def blue():
    return render_template("blue.html")

@app.route("/profile")
def profile():
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT * FROM chirps WHERE username = ?", (username, ))
    chirps = c.fetchall()
    c.execute("SELECT * FROM users WHERE username = ?", (username, ))
    user_info = c.fetchall()[0]
    return render_template("profile.html",user_info=user_info, username=username, chirps=chirps)

@app.route("/more")
def more():
    return render_template("more.html")

@app.route("/follow/<to_follow>")
def follow(to_follow):
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE LOWER(username) = ?", (to_follow.lower(),))
    user_query = c.fetchall()
    to_follow_case = user_query[0][0]
    c.execute("INSERT INTO followers (user, follower) VALUES (?, ?)", (to_follow_case, username))
    conn.commit()
    return redirect("/home")

@app.route("/search", methods=["GET", "POST"])
def search():
    search_query = request.form.get("search")
    print(search_query)
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username LIKE ?", (search_query,))
    db_results = c.fetchall()
    print(db_results)
    return render_template("search.html", accounts=db_results)



if __name__ == "__main__":
    app.run(debug=True)

