from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
import time
import datetime

#flask sqlalchemy attempt

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

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chirper2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CONFIGURE TABLES
with app.app_context():
    class Users(db.Model):
        __tablename__ = "users"
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(250), nullable=False, unique=True)
        password_hash = db.Column(db.String(250), nullable=False)
        joined_date = db.Column(db.String(250), nullable=False)
        following_num = db.Column(db.Integer, nullable=False)
        followers_num = db.Column(db.Integer, nullable=False)
        bio = db.Column(db.String(500), nullable=True)
        pro_pic = db.Column(db.String(1000), nullable=True)
        banner_pic = db.Column(db.String(1000), nullable=True)
        chirps = db.relationship('Chirps', backref='users')
        replies = db.relationship('Replies', backref='users')

    class Followers(db.Model):
        __tablename__ = "followers"
        id = db.Column(db.Integer, primary_key=True)
        user = db.Column(db.String(100), nullable=False)
        follower = db.Column(db.String(100), nullable=False)

    class Bookmarks(db.Model):
        __tablename__ = "bookmarks"
        id = db.Column(db.Integer, primary_key=True)
        user = db.Column(db.String(100), nullable=False)
        chirp_id = db.Column(db.Integer, nullable=False)

    class Chirps(db.Model):
        __tablename__ = "chirps"
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(100), nullable=False)
        user_pro_pic = db.Column(db.String(1000), nullable=True)
        text_content = db.Column(db.String(500), nullable=True)
        media_content = db.Column(db.String(1000), nullable=True)
        date_num = db.Column(db.Float, nullable=False)
        date_date = db.Column(db.String(100), nullable=False)
        likes = db.Column(db.Integer, nullable=True)
        original_by = db.Column(db.String(100), nullable=True)
        original_date_date = db.Column(db.String(100), nullable=True)
        original_id = db.Column(db.Integer, nullable=True)
        user_id = db.Column(db.Integer, db.ForeignKey(Users.id))

    class Replies(db.Model):
        __tablename__ = "replies"
        id = db.Column(db.Integer, primary_key=True)
        chirp_id = db.Column(db.Integer, nullable=False)
        username = db.Column(db.String(100), nullable=False)
        text_content = db.Column(db.String(500), nullable=True)
        media_content = db.Column(db.String(1000), nullable=True)
        date_num = db.Column(db.Float, nullable=False)
        date_date = db.Column(db.String(100), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey(Users.id))

    class Notifications(db.Model):
        __tablename__ = "notifications"
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(100), nullable=False)
        chirp_id = db.Column(db.Integer, nullable=True)
        doer = db.Column(db.String(100), nullable=False)
        date_num = db.Column(db.Float, nullable=False)
        date_date = db.Column(db.String(100), nullable=False)
        followed = db.Column(db.Boolean, nullable=True)
        retweeted = db.Column(db.Boolean, nullable=True)
        liked = db.Column(db.Boolean, nullable=True)

    class Likes(db.Model):
        __tablename__ = "likes"
        id = db.Column(db.Integer, primary_key=True)
        chirp_id = db.Column(db.Integer, nullable=False)
        username = db.Column(db.String(100), nullable=False)

    db.create_all()



def top3_accounts(username):
    '''Returns a list of top 3 accounts to follow by number of followers, excludes self
    and people you already follow'''
    # c.execute("SELECT * FROM users WHERE NOT username IN (SELECT user FROM followers WHERE follower = ?) AND username != ? ORDER BY followers DESC LIMIT 3", (username, username))
    following_accounts = [f.user for f in Followers.query.filter_by(follower=username)]
    top3 = Users.query.filter(Users.username.not_in(following_accounts), Users.username != username).order_by(Users.followers_num.desc()).limit(3).all()
    return top3



@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        sql_return = Users.query.filter_by(username=username).first()
        # no account with that username
        if not sql_return:
            flash("Could not find that username")
            return redirect("/")
        #valid username, check password
        if check_password_hash(sql_return.password_hash, password):
            session["username"] = username
            return redirect("/home")
        #valid username but incorrect password
        else:
            flash("Invalid password")
            return redirect("/")
    return render_template("login.html")



@app.route("/home", methods=["GET", "POST"])
def home():
    username = session["username"]
    if request.method == "POST":
        text_content = request.form.get("chirp")
        media_content = request.form.get("media")
        if not text_content and not media_content:
            return redirect("/home")
        date_num = time.time()
        date_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        user_id = Users.query.filter_by(username=username).first().id
        new_chirp = Chirps(
            username = username,
            text_content = text_content,
            media_content = media_content,
            date_num = date_num,
            date_date = date_date,
            likes = 0,
            user_id = user_id,
        )

        db.session.add(new_chirp)
        db.session.commit()
        return redirect("/home")


    following_list = [f.user for f in Followers.query.filter_by(follower=username)]
    query1 = Chirps.query.filter(Chirps.username.in_(following_list))
    query2 = Chirps.query.filter_by(username=username)
    chirps = query1.union(query2).order_by(Chirps.date_num.desc()).all()
    top_3 = top3_accounts(username)
    return render_template("index.html", chirps=chirps, top_3=top_3)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        print(len(username))
        print(len(password))
        if len(username) == 0 or len(password) == 0:
            flash('Please input valid username/password')
            redirect("register.html")

        # conn = sqlite3.connect("Chirper.db")
        # c = conn.cursor()

        #check if username already used, needs to be case-insensitive
        # c.execute("SELECT * FROM users WHERE LOWER(username) = ?", (username.lower(),))
        user_list = Users.query.filter(func.lower(Users.username) == username.lower()).first()
        print(user_list)
        if not user_list:
            password_hash = generate_password_hash(password)
            date = datetime.datetime.now().strftime("%B %Y")
            # c.execute("INSERT INTO users (username, password_hash, joined_date, following, followers) VALUES (?, ?, ?, ?, ?)", (username, password_hash, date, 0, 0))
            # conn.commit()
            new_user = Users(
                username = username,
                password_hash = password_hash,
                joined_date = date,
                following_num = 0,
                followers_num = 0,
                bio = "I am a boring person with no bio",
                pro_pic = "/static/profile.jpg",
                banner_pic = "/static/planets.jpeg"
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Successfully registered. Great job!')
            return redirect("/")
        flash('Username in use!')
        return render_template("register.html")
    return render_template("register.html")



@app.route("/reply/<int:chirp_id>", methods=["GET", "POST"])
def reply(chirp_id):
    username = session["username"]
    if request.method == "POST":
        text_content = request.form.get("reply")
        media_content = request.form.get("media")
        date_num = time.time()
        date_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_id = Users.query.filter_by(username=username).first().id
        new_reply = Replies(
            chirp_id = chirp_id,
            username = username,
            text_content = text_content,
            media_content = media_content,
            date_num = date_num,
            date_date = date_date,
            user_id = user_id,
        )
        db.session.add(new_reply)
        db.session.commit()
        return redirect(url_for("reply", chirp_id=chirp_id))

    chirp = Chirps.query.filter(Chirps.id == chirp_id).first()
    replies = Replies.query.filter_by(chirp_id=chirp_id).all()
    return render_template("reply.html", chirp=chirp, replies=replies)

@app.route("/account/<to_follow>")
def account(to_follow):
    username = session["username"]

    #get all of the accounts chirps
    chirps = Chirps.query.filter_by(username=to_follow).order_by(Chirps.date_num.desc()).all()
    #get the accounts info
    user_info = Users.query.filter_by(username=to_follow).first()
    #check to see if following
    is_following_query = Followers.query.filter(Followers.user == to_follow, Followers.follower == username).first()
    is_following = False
    if is_following_query:
        is_following = True
    #check to see if on own account page so that you dont follow self
    not_self = True
    if username == to_follow:
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
    my_notifications = Notifications.query.filter(Notifications.username == username).order_by(Notifications.date_num.desc()).limit(5).all()
    print(my_notifications)

    return render_template("notifications.html", top_3=top3, my_notifications=my_notifications)

@app.route("/delete_notif/<notif_id>")
def delete_notif(notif_id):
    notif_to_delete = Notifications.query.filter_by(id=notif_id).first()
    db.session.delete(notif_to_delete)
    db.session.commit()
    return redirect("/notifications")

@app.route("/messages")
def messages():
    username = session["username"]
    top3 = top3_accounts(username)
    return render_template("messages.html", top_3=top3)

@app.route("/bookmarkverb/<chirp_id>")
def bookmark_verb(chirp_id):
    username = session["username"]
    new_bookmark = Bookmarks(
        user = username,
        chirp_id = chirp_id
    )
    db.session.add(new_bookmark)
    db.session.commit()

    return redirect("/home")

@app.route("/del_bookmark/<chirp_id>")
def del_bookmark(chirp_id):
    username = session["username"]
    bookmark_to_delete = Bookmarks.query.filter(Bookmarks.user == username, Bookmarks.chirp_id == chirp_id).first()
    db.session.delete(bookmark_to_delete)
    db.session.commit()
    return redirect("/bookmarks")

@app.route("/bookmarks")
def bookmarks():
    username = session["username"]
    chirp_ids = [b.chirp_id for b in Bookmarks.query.filter_by(user=username).all()]
    marked = Chirps.query.filter(Chirps.id.in_(chirp_ids)).all()
    print(marked)
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
    # conn = sqlite3.connect("Chirper.db")
    # c = conn.cursor()
    # c.execute("SELECT * FROM chirps WHERE username = ? ORDER BY date_num DESC", (username, ))
    # chirps = c.fetchall()
    # c.execute("SELECT * FROM users WHERE username = ?", (username, ))
    # user_info = c.fetchall()[0]

    #get user info
    user_info = Users.query.filter_by(username=username).first()
    print(user_info)
    #get users chirps
    chirps = Chirps.query.filter_by(username=username).order_by(Chirps.date_num.desc()).all()
    top3 = top3_accounts(username)
    return render_template("profile.html", top_3=top3, user_info=user_info, username=username, chirps=chirps)

@app.route("/setup", methods=["GET", "POST"])
def setup():
    username = session["username"]
    if request.method == "POST":
        propic = request.form.get("propic")
        bio = request.form.get("bio")
        banner = request.form.get("banner")
        Users.query.filter_by(username=username).update({'bio': bio, 'pro_pic': propic, "banner_pic": banner})
        db.session.commit()
        return redirect("/home")
    user_info = Users.query.filter_by(username=username).first()
    top3 = top3_accounts(username)
    return render_template("setup.html", user_info=user_info, top_3=top3)



@app.route("/follow/<to_follow>")
def follow(to_follow):
    username = session["username"]
    #add new follower
    new_follower = Followers(
        user = to_follow,
        follower = username
    )
    db.session.add(new_follower)
    db.session.commit()

    #update follower counts
    current_user_following = Users.query.filter_by(username=username).first().following_num
    print(current_user_following)
    current_user_following += 1
    Users.query.filter_by(username=username).update({"following_num": current_user_following})
    current_to_follow_followers = Users.query.filter_by(username=to_follow).first().followers_num
    current_to_follow_followers += 1
    Users.query.filter_by(username=to_follow).update({"followers_num": current_to_follow_followers})
    print(current_to_follow_followers)
    db.session.commit()
    #update notifications
    date_num = time.time()
    date_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_notification = Notifications(
        username = to_follow,
        doer = username,
        date_num = date_num,
        date_date = date_date,
        followed = True
    )
    print("adding new notification")
    print(new_notification)
    db.session.add(new_notification)
    db.session.commit()
    return redirect("/home")

@app.route("/following/<account>")
def following(account):
    #show all the people you are following
    following_accounts = [f.user for f in Followers.query.filter_by(follower=account)]
    accounts = Users.query.filter(Users.username.in_(following_accounts)).all()
    at_following = True
    username = session["username"]
    top3 = top3_accounts(username)
    return render_template("followinger.html", accounts=accounts, at_following=at_following, top_3=top3)

@app.route("/follower/<account>")
def followers(account):
    #show all the people following you
    following_accounts = [f.follower for f in Followers.query.filter_by(user=account)]
    accounts = Users.query.filter(Users.username.in_(following_accounts)).all()
    at_following = False
    username = session["username"]
    top3 = top3_accounts(username)
    return render_template("followinger.html", top_3=top3, accounts=accounts, at_following=at_following)

@app.route("/unfollow/<to_follow>")
def unfollow(to_follow):
    username = session["username"]

    follower_to_delete = Followers.query.filter(Followers.user == to_follow, Followers.follower == username).first()
    db.session.delete(follower_to_delete)
    db.session.commit()
    #update follower counts
    current_follower_count = Users.query.filter_by(username=to_follow).first().followers_num
    current_follower_count -= 1
    Users.query.filter_by(username=to_follow).update({'followers_num': current_follower_count})

    current_following_count = Users.query.filter_by(username=to_follow).first().following_num
    current_following_count -= 1
    Users.query.filter_by(username=username).update({'following_num': current_following_count})
    db.session.commit()
    return redirect("/home")


@app.route("/search", methods=["GET", "POST"])
def search():
    search_query = request.form.get("search")
    db_results = Users.query.filter(Users.username.like(search_query)).all()
    username = session["username"]
    top3 = top3_accounts(username)
    return render_template("search.html", top_3=top3, accounts=db_results)

@app.route("/rechirp/<chirp_id>")
def rechirp(chirp_id):
    username = session["username"]
    #check if already retweeted so that you cant retweet again, if so remove?
    check = Chirps.query.filter(Chirps.username == username, Chirps.original_id == chirp_id).first()
    print(check)
    if check:
        db.session.delete(check)
        db.session.commit()
        return redirect("/home")
    #if not make a new retweet
    chirp_of_interest = Chirps.query.filter_by(id=chirp_id).first()
    new_date_num = time.time()
    new_date_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_chirp = Chirps(
        username = username,
        original_by = chirp_of_interest.username,
        original_id = chirp_id,
        original_date_date = chirp_of_interest.date_date,
        text_content = chirp_of_interest.text_content,
        media_content = chirp_of_interest.media_content,
        date_num = new_date_num,
        date_date = new_date_date,
        likes = 0,

    )
    db.session.add(new_chirp)
    db.session.commit()

    #update notifications
    new_notification = Notifications(
        username = chirp_of_interest.username,
        chirp_id = chirp_id,
        doer = username,
        date_num = new_date_num,
        date_date = new_date_date,
        retweeted = True,
    )
    db.session.add(new_notification)
    db.session.commit()
    return redirect("/home")

@app.route("/like/<chirp_id>")
def like(chirp_id):
    username = session["username"]
    #check to see if already liked
    is_liked = Likes.query.filter(Likes.username == username, Likes.chirp_id == chirp_id).first()

    if not is_liked:
        new_like = Likes(
            chirp_id = chirp_id,
            username = username
        )
        db.session.add(new_like)
        current_chirp_likes = Chirps.query.filter_by(id=chirp_id).first().likes
        current_chirp_likes += 1
        Chirps.query.filter_by(id=chirp_id).update({"likes": current_chirp_likes})
        db.session.commit()
    else:
        like_to_remove = Likes.query.filter(Likes.username == username, Likes.chirp_id == chirp_id).first()
        db.session.delete(like_to_remove)
        current_chirp_likes = Chirps.query.filter_by(id=chirp_id).first().likes
        current_chirp_likes -= 1
        Chirps.query.filter_by(id=chirp_id).update({"likes": current_chirp_likes})
        db.session.commit()
    return redirect("/home")

if __name__ == "__main__":
    app.run(debug=True)

