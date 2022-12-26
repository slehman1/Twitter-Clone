from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import time
import datetime

#sqlite attempt

app = Flask(__name__)

# conn = sqlite3.connect("Chirper.db")
# c = conn.cursor()
# c.execute("CREATE TABLE chirps (chirp_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, text_content TEXT, media_content TEXT, date_num NUMERIC NOT NULL, date_date TEXT NOT NULL)")
# c.execute("CREATE TABLE followers (user TEXT NOT NULL, follower TEXT NOT NULL)")
# c.execute("CREATE TABLE replies (chirp_id INTEGER NOT NULL, username TEXT NOT NULL, text_content TEXT NOT NULL, media_content TEXT NOT NULL, date_num NUMERIC NOT NULL, date_date TEXT NOT NULL)")
# c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, password_hash TEXT NOT NULL, joined_date TEXT NOT NULL, following INTEGER, followers INTEGER, bio TEXT, pro_pic TEXT, banner_pic TEXT)")
# c.execute("CREATE TABLE bookmarks (username TEXT NOT NULL, chirp_id INTEGER NOT NULL)")
# c.execute("CREATE TABLE notifications (username TEXT NOT NULL, doer TEXT NOT NULL, date_num NUMERIC NOT NULL, date_date TEXT NOT NULL, followed INTEGER, retweeted INTEGER, liked INTEGER, chirp_id INTEGER)")

app.secret_key = "oh_hi_mark_oh_hi_doggy"

def top3_accounts(username):
    '''Returns a list of top 3 accounts to follow by number of followers, excludes self
    and people you already follow'''
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE NOT username IN (SELECT user FROM followers WHERE follower = ?) AND username != ? ORDER BY followers DESC LIMIT 3", (username, username))
    top3 = c.fetchall()
    print(top3)
    conn.close()
    return top3



@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        session["username"] = username
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
    username = session["username"]
    if request.method == "POST":
        text_content = request.form.get("chirp")
        media_content = request.form.get("media")
        date_num = time.time()
        date_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("Chirper.db")
        c = conn.cursor()
        c.execute("INSERT INTO chirps (username, text_content, media_content, date_num, date_date) VALUES (?, ?, ?, ?, ?)", (username, text_content, media_content, date_num, date_date))
        conn.commit()
        c.close()
        return redirect("/home")
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT * FROM chirps WHERE username IN (SELECT user FROM followers WHERE follower = ?) UNION SELECT * FROM chirps WHERE username = ? ORDER BY date_num DESC", (username, username))
    chirps = c.fetchall()
    print(chirps)
    top_3 = top3_accounts(username)
    c.close()
    return render_template("index.html", chirps=chirps, top_3=top_3)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if len(username) == 0 or len(password) == 0:
            redirect("register.html")

        conn = sqlite3.connect("Chirper.db")
        c = conn.cursor()
        #check if username already used, needs to be case-insensitive
        c.execute("SELECT * FROM users WHERE LOWER(username) = ?", (username.lower(),))
        user_list = c.fetchall()
        print(user_list)
        if not user_list:
            password_hash = generate_password_hash(password)
            date = datetime.datetime.now().strftime("%B %Y")
            c.execute("INSERT INTO users (username, password_hash, joined_date, following, followers) VALUES (?, ?, ?, ?, ?)", (username, password_hash, date, 0, 0))
            conn.commit()
            return redirect("/")
        return render_template("register.html")
    return render_template("register.html")



@app.route("/reply/<int:chirp_id>", methods=["GET", "POST"])
def reply(chirp_id):
    username = session["username"]
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
    username = session["username"]
    lower_to_follow = to_follow.lower()
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    #get all of the accounts chirps
    c.execute("SELECT * FROM chirps WHERE LOWER(username) = ? ORDER BY date_num DESC", (lower_to_follow,))
    chirps = c.fetchall()
    #get the accounts info
    c.execute("SELECT * FROM users WHERE LOWER(username) = ?", (lower_to_follow,))
    user_info = c.fetchall()[0]
    #check to see if following
    c.execute("SELECT * FROM followers WHERE LOWER(user) = ? AND follower = ?", (lower_to_follow, username))
    is_following_query = c.fetchall()
    is_following = False
    if is_following_query:
        is_following = True
    c.close()
    #check to see if on own account page so that you dont follow self
    not_self = True
    if username.lower() == lower_to_follow:
        not_self = False
    top3 = top3_accounts(username)
    return render_template("account.html", top_3=top3, user_info=user_info, is_following=is_following, to_follow=to_follow, chirps=chirps, not_self=not_self)



@app.route("/explore")
def explore():
    username = session["username"]
    top3 = top3_accounts(username)
    return render_template("explore.html", top_3=top3)

@app.route("/notifications")
def notifications():
    #goal is to render top5 most recent notifications
    username = session["username"]
    top3 = top3_accounts(username)
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT * FROM notifications WHERE username = ? ORDER BY date_num DESC LIMIT 5", (username,))
    my_notifications = c.fetchall()
    print(my_notifications)


    return render_template("notifications.html", top_3=top3, my_notifications=my_notifications)

@app.route("/messages")
def messages():
    username = session["username"]
    top3 = top3_accounts(username)
    return render_template("messages.html", top_3=top3)

@app.route("/bookmarkverb/<chirp_id>")
def bookmark_verb(chirp_id):
    username = session["username"]
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("INSERT into bookmarks (username, chirp_id) VALUES (?, ?)", (username, chirp_id))
    conn.commit()
    conn.close()

    return redirect("/home")

@app.route("/bookmarks")
def bookmarks():
    username = session["username"]
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT * FROM chirps WHERE chirp_id IN (SELECT chirp_id FROM bookmarks WHERE username = ?)", (username,))
    marked = c.fetchall()
    print(marked)
    conn.close()
    top3 = top3_accounts(username)
    return render_template("bookmarks.html", marked=marked, top_3=top3)

@app.route("/blue")
def blue():
    username = session["username"]
    top3 = top3_accounts(username)
    return render_template("blue.html", top_3=top3)

@app.route("/profile")
def profile():
    username = session["username"]
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT * FROM chirps WHERE username = ? ORDER BY date_num DESC", (username, ))
    chirps = c.fetchall()
    c.execute("SELECT * FROM users WHERE username = ?", (username, ))
    user_info = c.fetchall()[0]
    print(user_info)
    top3 = top3_accounts(username)
    return render_template("profile.html", top_3=top3, user_info=user_info, username=username, chirps=chirps)

@app.route("/setup", methods=["GET", "POST"])
def setup():
    username = session["username"]
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    if request.method == "POST":
        propic = request.form.get("propic")
        print(propic)
        bio = request.form.get("bio")
        print(bio)
        banner = request.form.get("banner")
        print(banner)
        print(username)
        c.execute("UPDATE users SET bio = ?, pro_pic = ?, banner_pic = ? WHERE username = ?", (bio, propic, banner, username))
        print("here")
        conn.commit()
        conn.close()
        return redirect("/home")
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_info = c.fetchall()[0]
    conn.close()
    top3 = top3_accounts(username)
    return render_template("setup.html", user_info=user_info, top_3=top3)



@app.route("/follow/<to_follow>")
def follow(to_follow):
    username = session["username"]
    #to follow variable passes back incorrect case
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE LOWER(username) = ?", (to_follow.lower(),))
    user_query = c.fetchall()
    to_follow_case = user_query[0][0]
    c.execute("INSERT INTO followers (user, follower) VALUES (?, ?)", (to_follow_case, username))
    #update follower counts
    c.execute("SELECT followers FROM users WHERE username = ?", (to_follow_case,))
    follower_count = c.fetchall()[0][0]
    follower_count += 1
    c.execute("UPDATE users SET followers = ? WHERE username = ?", (follower_count, to_follow_case))
    conn.commit()
    c.execute("SELECT following FROM users WHERE username = ?", (username,))
    following_count = c.fetchall()[0][0]
    following_count += 1
    c.execute("UPDATE users SET following = ? WHERE username = ?", (following_count, username))
    conn.commit()
    #update notifications
    date_num = time.time()
    date_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO notifications (username, doer, followed, date_num, date_date) VALUES (?, ?, ?, ?, ?)", (to_follow_case, username, 1, date_num, date_date))
    conn.commit()
    conn.close()
    return redirect("/home")

@app.route("/following/<account>")
def following(account):
    #show all the people you are following
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username IN (SELECT user FROM followers WHERE follower = ?)", (account,))
    accounts = c.fetchall()
    print(accounts)
    at_following = True
    username = session["username"]
    top3 = top3_accounts(username)
    return render_template("followinger.html", accounts=accounts, at_following=at_following, top_3=top3)

@app.route("/follower/<account>")
def followers(account):
    #show all the people you are following
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username IN (SELECT follower FROM followers WHERE user = ?)", (account,))
    accounts = c.fetchall()
    print(accounts)
    at_following = False
    username = session["username"]
    top3 = top3_accounts(username)
    return render_template("followinger.html", top_3=top3, accounts=accounts, at_following=at_following)

@app.route("/unfollow/<to_follow>")
def unfollow(to_follow):
    username = session["username"]
    conn = sqlite3.connect("Chirper.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE LOWER(username) = ?", (to_follow.lower(),))
    user_query = c.fetchall()
    to_follow_case = user_query[0][0]
    print(to_follow_case)
    c.execute("DELETE FROM followers WHERE user = ? AND follower = ?", (to_follow_case, username))
    #update follower counts
    c.execute("SELECT followers FROM users WHERE username = ?", (to_follow_case,))
    follower_count = c.fetchall()[0][0]
    follower_count -= 1
    c.execute("UPDATE users SET followers = ? WHERE username = ?", (follower_count, to_follow_case))
    conn.commit()
    c.execute("SELECT following FROM users WHERE username = ?", (username,))
    following_count = c.fetchall()[0][0]
    following_count -= 1
    c.execute("UPDATE users SET following = ? WHERE username = ?", (following_count, username))
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
    username = session["username"]
    top3 = top3_accounts(username)
    return render_template("search.html", top_3=top3, accounts=db_results)



if __name__ == "__main__":
    app.run(debug=True)

