import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime

from helpers import login_required, error, retrieve, is_int

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///fb.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    # Create the feed:
    # - Include the logged-in user's posts and posts from users they follow.
    # - Join with the Users table to display the author's username and profile picture.
    # - Count the number of likes, comments, and reposts for each post.
    # - Display the newest posts first.
    # Used AI to help me with this query
    posts = db.execute("""
        SELECT
            Posts.*,
            0 as is_repost,
            Users.username,
            Users.profile_picture,

            (
                SELECT COUNT(*)
                FROM Likes
                WHERE Likes.post_id = Posts.id
            ) AS likes_count,

            (
                SELECT COUNT(*)
                FROM Comments
                WHERE Comments.post_id = Posts.id
            ) AS comments_count,
                       
            (
                SELECT COUNT(*)
                FROM Likes
                WHERE Likes.post_id = Posts.id
                AND Likes.user_id = ?
            ) AS is_liked,

            (
                SELECT COUNT(*)
                FROM Reposts
                WHERE Reposts.post_id = Posts.id
            ) AS reposts_count,
                       
            NULL AS reposted_by,
            NULL AS repost_text,
                       
            Posts.created_at AS feed_time

        FROM Posts
        JOIN Users
            ON Posts.user_id = Users.id

        WHERE Posts.user_id = ?
        OR Posts.user_id IN (
                SELECT following_id
                FROM Follows
                WHERE follower_id = ?
        )
                       
        UNION ALL

        SELECT
            Posts.*,
            1 AS is_repost,             
            Users.username,
            Users.profile_picture,

            (
                SELECT COUNT(*)
                FROM Likes
                WHERE Likes.post_id = Reposts.post_id
            ) AS likes_count,

            (
                SELECT COUNT(*)
                FROM Comments
                WHERE Comments.post_id = Reposts.post_id
            ) AS comments_count,
                       
            (
                SELECT COUNT(*)
                FROM Likes
                WHERE Likes.post_id = Posts.id
                AND Likes.user_id = ?
            ) AS is_liked,

            (
                SELECT COUNT(*)
                FROM Reposts
                WHERE Reposts.post_id = Posts.id
            ) AS reposts_count,
                       
            (
                SELECT username
                FROM Users
                WHERE Users.id = Reposts.user_id
            ) AS reposted_by,
                       
            Reposts.text AS repost_text,
            Reposts.created_at AS feed_time
                       
        FROM Reposts
        JOIN Posts
        ON Reposts.post_id = Posts.id
        JOIN Users
        ON Posts.user_id = Users.id
                       
        WHERE Reposts.user_id = ?
        OR Reposts.user_id IN (
                SELECT following_id
                FROM Follows
                WHERE follower_id = ?
        )
                       
        ORDER BY feed_time DESC
    """, session["user_id"], session["user_id"], session["user_id"],
      session["user_id"], session["user_id"], session["user_id"])

    return render_template("index.html", posts=posts)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in""" 
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("login.html")

    # Forget any user_id
    session.clear()
    # Ensure username was submitted
    if not request.form.get("username"):
        return error("Must enter username", "danger", "/login")

    # Ensure password was submitted
    password = request.form.get("password", "")
    if not password:
        return error("Must enter password", "danger", "/login")

    # Query database
    username = request.form.get("username", "")
    rows = db.execute(
        "SELECT * FROM Users WHERE username = ?", username
    )

    # Ensure username exists and password is correct
    if len(rows) != 1 or not check_password_hash(
        rows[0]["password_hash"], password
    ):
        # invalid username and/or password
        return error("Invalid username and/or password", "danger", "/login")

    # Remember which user has logged in
    session["user_id"] = rows[0]["id"]
    session["user_name"] = rows[0]["username"]

    # Welcome the user
    flash(f"Welcome, {session["user_name"]}", "success")

    # Redirect user to home page
    return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register the user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate the input fields
        if not username: 
            return error("Must enter username", "danger", "/register")
        if not password:
            return error("Must enter password", "danger", "/register")
        if not confirmation:
            return error("Must enter confirmation", "danger", "/register")
        if not password == confirmation:
            return error("password and confirmation are not matching", "danger", "/register")
        
        # Generate a password hash for secure storage
        password_hash = generate_password_hash(password)

        # Attempt to insert the new user into the database, if the username already exists, return an error
        try:
            db.execute("INSERT INTO Users (username, password_hash) VALUES (?, ?);", username, password_hash)
        except ValueError:
            return error("Username already exist", "danger", "/register")
        
        flash("You are now part of Mini Facebook!", "success")

        return render_template("login.html")
    return render_template("register.html")


@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    if request.method == "POST":
        # Query database for user's info
        rows = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"]
        )

        # Ensure old password exists and is correct
        oldpassword = request.form.get("oldpassword")
        if not oldpassword:
            return error("Must enter oldpassword", "danger", "/change")
        if not check_password_hash(
            rows[0]["password_hash"], str(oldpassword)
        ):
            return error("Invalid old password", "danger", "/change")

        newpassword = request.form.get("newpassword")
        confirmation = request.form.get("confirmation")

        # Validate the input fields
        if not newpassword:
            return error("Must enter new password", "danger", "/change")
        if check_password_hash(rows[0]["password_hash"], newpassword):
            return error("New password must be different", "danger", "/change")
        if not confirmation:
            return error("Must enter confirmation", "danger", "/change")
        if not newpassword == confirmation:
            return error("Password and confirmation are not matching", "danger", "/change")

        # Generate a password hash for secure storage
        password_hash = generate_password_hash(newpassword)

        # Updating the user's password
        db.execute("UPDATE Users SET password_hash = ? WHERE id = ?", password_hash, session["user_id"])
        flash("Password changed!", "success")

        return redirect("/")
    return render_template("change.html")


@app.route("/search")
@login_required
def search():
    # Get the search query from the URL
    query = request.args.get("q")

    # Ensure the user entered a username to search for
    if not query:
        return error("Invalid operation or must type in a username", "danger", "/")
    
    # Remove any leading or trailing whitespace
    query = query.strip()
    
    # Ensure the search query is not only whitespace
    if not query:
        return error("Must type in a username", "danger", "/")
    
    # Enforce the maximum username length
    if len(query) > 20:
        return error("Limit exceeded", "danger", "/")

    # Retrieve all users (except the current user) whose usernames
    # contain the search query, ignoring letter case
    users = db.execute(
        "SELECT * FROM Users WHERE id != ? AND LOWER(username) LIKE LOWER(?)",
        session["user_id"],
        "%" + str(query) + "%"
    )

    # Display the search results
    return render_template("search.html", users=users)


@app.route("/profile/<int:user_id>")
@login_required
def profile(user_id):
    # Retrieve the requested user's information
    user = retrieve(user_id, "Users")
    if not user:
        return error("User does not exist", "danger", "/")

    # Retrieve all original posts and reposts made by the user,
    # along with their likes, comments, repost counts, and whether
    # the logged-in user has liked each post
    # AI helped me with this query
    posts = db.execute("""
            SELECT Posts.*,
                0 as is_repost,
                        
                (
                    SELECT COUNT(*)
                    FROM Likes
                    WHERE Likes.post_id = Posts.id
                ) AS likes_count,

                (
                    SELECT COUNT(*)
                    FROM Comments
                    WHERE Comments.post_id = Posts.id
                ) AS comments_count,

                (
                    SELECT COUNT(*)
                    FROM Reposts
                    WHERE Reposts.post_id = Posts.id
                ) AS reposts_count,
                       
                (
                    SELECT COUNT(*)
                    FROM Likes
                    WHERE Likes.post_id = Posts.id
                    AND Likes.user_id = ?
                ) AS is_liked,
                        
                NULL AS reposted_by,
                NULL AS repost_text,
                        
                Posts.created_at AS feed_time
            
            FROM Posts WHERE user_id = ? 
                       
        UNION ALL
                       
            SELECT Posts.*,
                1 AS is_repost,             

                (
                    SELECT COUNT(*)
                    FROM Likes
                    WHERE Likes.post_id = Reposts.post_id
                ) AS likes_count,

                (
                    SELECT COUNT(*)
                    FROM Comments
                    WHERE Comments.post_id = Reposts.post_id
                ) AS comments_count,

                (
                    SELECT COUNT(*)
                    FROM Reposts
                    WHERE Reposts.post_id = Posts.id
                ) AS reposts_count,
                        
                (
                    SELECT COUNT(*)
                    FROM Likes
                    WHERE Likes.post_id = Posts.id
                    AND Likes.user_id = ?
                ) AS is_liked,            
                
                (
                    SELECT username
                    FROM Users
                    WHERE Users.id = Reposts.user_id
                ) AS reposted_by,
                        
                Reposts.text AS repost_text,
                Reposts.created_at AS feed_time
                        
            FROM Reposts
            JOIN Posts
                ON Reposts.post_id = Posts.id
            WHERE Reposts.user_id = ?
                       
        ORDER BY feed_time DESC""", user_id, user_id, user_id, user_id)

    # Count the total number of posts and reposts made by the user
    posts_count = (
        db.execute(
            "SELECT COUNT(*) AS count FROM Posts WHERE user_id = ?",
            user_id
        )[0]["count"]
        +
        db.execute(
            "SELECT COUNT(*) AS count FROM Reposts WHERE user_id = ?",
            user_id
        )[0]["count"]
    )

    # Count the user's followers
    followers = db.execute("SELECT COUNT(*) as followers FROM Follows WHERE following_id = ?", user_id)[0]["followers"]

    # Count the users this user is following
    following = db.execute("SELECT COUNT(*) as following FROM Follows WHERE follower_id = ?", user_id)[0]["following"]

    # Check whether the logged-in user follows this profile
    is_followed = bool(
        db.execute(
            "SELECT * FROM Follows WHERE follower_id = ? AND following_id = ?",
            session["user_id"],
            user_id
        )
    )

    # Display the user's profile page
    return render_template("profile.html", user=user, posts=posts,
                                posts_count=posts_count,
                                followers=followers,
                                following=following,
                                is_followed=is_followed)


@app.route("/following")
@login_required
def following():
    # Retrieve all users followed by the logged-in user
    following = db.execute("""
                            SELECT Users.*
                            FROM Follows
                            JOIN Users
                                ON Follows.following_id = Users.id
                            WHERE Follows.follower_id = ?
                        """, session["user_id"])

    # Display the list of followed users
    return render_template("following.html", following=following)


@app.route("/follow", methods=["GET", "POST"])
@login_required
def follow():
    # User submitted the follow request
    if request.method == "POST":
        # Get the IDs of the follower and the user to follow
        follower_id = session["user_id"]
        following_id = request.form.get("user_id")

        # Ensure a user ID was provided
        if not following_id:
            return error("Invalid operation", "danger", "/")
        
        # Ensure the provided user ID is a valid integer
        if not is_int(following_id):
            return error("Invalid operation", "danger", "/")
            

        # Prevent users from following themselves
        if follower_id == following_id:
            return error("You can not follow yourself", "danger", f"/profile/{session["user_id"]}")
        
        # Ensure the target user exists
        user = retrieve(following_id, "Users")
        if not user:
            return error("User does not exist", "danger", "/")

        # Create the follow relationship
        try:
            db.execute("INSERT INTO Follows (follower_id, following_id) VALUES (?, ?)", follower_id, following_id)
        except ValueError:
            # The user is already following the target user
            return error("You are already following this user", "danger", f"/profile/{following_id}")
        
        # Notify the user that the follow was successful
        flash("You are now following this user!", "success")

        # Return to the followed user's profile
        return redirect(f"/profile/{following_id}")

    # Redirect GET requests to the following page
    return redirect("/following")


@app.route("/unfollow", methods=["GET", "POST"])
@login_required
def unfollow():
    # User submitted the unfollow request
    if request.method == "POST":
        # Get the IDs of the follower and the user to unfollow
        follower_id = session["user_id"]
        following_id = request.form.get("user_id")

        # Ensure a user ID was provided
        if not following_id:
            return error("Invalid operation", "danger", "/")
        
        # Ensure the provided user ID is a valid integer
        if not is_int(following_id):
            return error("Invalid operation", "danger", "/")
        
        # Prevent users from unfollowing themselves
        if follower_id == following_id:
            return error("Invalid operation", "danger", "/")
        
        # Ensure the target user exists
        user = retrieve(following_id, "Users")
        if not user:
            return error("User does not exist", "danger", "/")
        
        # Ensure the current user is actually following the target user
        follow = db.execute(
            "SELECT * FROM Follows WHERE follower_id = ? AND following_id = ?",
            follower_id,
            following_id
        )

        if not follow:
            return error("You are not following this user", "danger", "/")

        # Remove the follow relationship
        db.execute("DELETE FROM Follows WHERE follower_id = ? AND following_id = ?", follower_id, following_id)
        
        # Notify the user that the unfollow was successful
        flash("You are not following this user anymore!", "success")

        # Return to the unfollowed user's profile
        return redirect(f"/profile/{following_id}")
    
    # Redirect GET requests to the following page
    return redirect("/following")


# All below are done
@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    # Retrieve the logged-in user's information
    user = db.execute("SELECT * FROM Users WHERE id = ?", session["user_id"])

    # User submitted changes to their profile
    if request.method == "POST":
        # Get the updated username 
        new_username = request.form.get("username")
        
        # Check that new username is not empty
        if not new_username:
            flash("Invalid operation or must enter a new username", "danger")
        # Update the username if a new one was provided
        elif new_username.strip() and new_username != user[0]["username"]:
            # Ensure the username does not exceed the maximum length
            if len(new_username) <= 20:
                try:
                    # Update the username in the database
                    db.execute("UPDATE Users SET username = ? WHERE id = ?", new_username, session["user_id"])
                    # Update the username stored in the current session
                    session["user_name"] = new_username
                except ValueError:
                    # Username already exists
                    flash("Username already exists...", "danger")
            else:
                flash("Limit exceeded", "danger")

        # Get the updated profile picture
        new_picture = request.files.get("profile_picture")

        # Remove the current profile picture if requested
        # Used AI to help me the path for images and delete them
        if request.form.get("remove_picture"):
            old_img = f"static/profile_pictures/{user[0]['profile_picture']}"
            if os.path.exists(old_img):
                os.remove(old_img)

            db.execute("UPDATE Users SET profile_picture = NULL WHERE id = ?", session["user_id"])

        # Update the profile picture if a new one was uploaded
        elif new_picture and new_picture.filename:
            # Make sure it's an actual image and not a malicious file
            # Used AI to help me verify images
            try:
                img = Image.open(new_picture.stream)
                img.verify()

                # Reset the stream just in case the saved file is empty or corrupted.
                new_picture.stream.seek(0)
            except Exception:
                return error("Invalid image", "danger", "/")
            
            # Delete the previous profile picture if it exists
            old_img = f"static/profile_pictures/{user[0]['profile_picture']}"
            if os.path.exists(old_img):
                os.remove(old_img)
            
            # Save the new profile picture and update the database
            filename = secure_filename(new_picture.filename)
            new_picture.save(f"static/profile_pictures/{filename}")
            db.execute("UPDATE Users SET profile_picture = ? WHERE id = ?", filename, session["user_id"])

        # Get the updated bio
        new_bio = request.form.get("new_bio")

        # Update the bio if it has changed
        if new_bio != user[0]["bio"]:
            db.execute("UPDATE Users SET bio = ? WHERE id = ?", new_bio, session["user_id"])

        # Get the updated birthday
        new_birthday = request.form.get("birthday")

        # Validate and update the birthday if it has changed
        if new_birthday != user[0]["birthday"]:
            try:
                if new_birthday:
                    datetime.strptime(new_birthday, "%Y-%m-%d")
                    db.execute("UPDATE Users SET birthday = ? WHERE id = ?", new_birthday, session["user_id"])
                else:
                    db.execute("UPDATE Users SET birthday = NULL WHERE id = ?", session["user_id"])
            except ValueError:
                flash("new_birthday: invalid operation", "danger")

        # Get the updated relationship status
        new_status = request.form.get("relationship")
        valid_status = ["", "Single", "In a relationship", "Engaged", "Married"]

        # Update the relationship status only if it is valid and has changed
        if new_status != user[0]["relationship"] and new_status in valid_status:
            db.execute("UPDATE Users SET relationship = ? WHERE id = ?", new_status, session["user_id"])
            
        # Get the updated location
        new_location = request.form.get("location")

        # Update the location if it has changed
        if new_location != user[0]["location"]:
            db.execute("UPDATE Users SET location = ? WHERE id = ?", new_location, session["user_id"])
        
        # Get the updated education
        new_education = request.form.get("education")

        # Update the education if it has changed
        if new_education != user[0]["education"]:
            db.execute("UPDATE Users SET education = ? WHERE id = ?", new_education, session["user_id"])
    
        # Get the updated job
        new_job = request.form.get("job")

        # Update the job if it has changed
        if new_job != user[0]["job"]:
            db.execute("UPDATE Users SET job = ? WHERE id = ?", new_job, session["user_id"])

        # Notify the user that the profile has been updated
        flash("Profile updated successfully!", "success")

        # Redirect to the user's profile page
        return redirect(f"/profile/{session["user_id"]}")

    # Display the edit profile page
    return render_template("edit.html", user=user[0])


@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create():
    # User submitted the create request
    if request.method == "POST":
        # Get the post content and optional uploaded image
        content = request.form.get("content")
        photo = request.files.get("post_image")        

        # Ensure the content field was submitted
        if not content:
            return error("Invalid operation or posts must contain text", "danger", "/")
        
        # Reject posts containing only whitespace
        if not content.strip():
            return error("Posts must contain text", "danger", "/")
        
        # Enforce the maximum allowed post length
        if len(content) > 5000:
            return error("Limit exceeded", "danger", "/")

        # Save the post with an image if one was uploaded
        if photo and photo.filename:
            # Make sure it's an actual image and not a malicious file
            try:
                img = Image.open(photo.stream)
                img.verify()

                # Reset the stream just in case the saved file is empty or corrupted.
                photo.stream.seek(0)
            except Exception:
                return error("Invalid image", "danger", "/")
            
            # Save the uploaded image and create the post
            filename = secure_filename(photo.filename)
            photo.save(f"static/posts_pictures/{filename}")
            db.execute("INSERT INTO Posts (user_id, content, image, created_at) VALUES (?, ?, ?, ?);",
                        session["user_id"], content, filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        else:
            # Create a text-only post
            db.execute("INSERT INTO Posts (user_id, content, created_at) VALUES (?, ?, ?);",
                        session["user_id"], content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Notify the user that the post was created successfully
        flash("Posted successfully!", "success")
        return redirect("/")
    
    # Redirect GET requests to the home page
    return redirect("/")


@app.route("/delete_post", methods=["GET", "POST"])
@login_required
def delete():
    # User submitted the delete request
    if request.method == "POST":
        # Get the ID of the post to be deleted
        post_id = request.form.get("post_id")

        # Ensure the post exists
        post = retrieve(post_id, "Posts")
        if not post:
            return error("Post does not exist", "danger", "/")
        
        # Ensure the current user owns the post
        if not post["user_id"] == session["user_id"]:
            return error("Not authorized", "danger", "/")
        
        # Delete the post's image from storage if it exists
        if post["image"]:
            img = f"static/posts_pictures/{post['image']}"
            if os.path.exists(img):
                os.remove(img)
        
        # Delete all data associated with the post
        db.execute("DELETE FROM Likes WHERE post_id = ?", post_id)
        db.execute("DELETE FROM Comments WHERE post_id = ?", post_id)
        db.execute("DELETE FROM Reposts WHERE post_id = ?", post_id)
        db.execute("DELETE FROM Posts WHERE id = ?", post_id)

        # Notify the user that the post was deleted successfully
        flash("Post deleted successfully!", "success")
        return redirect(f"/")
    
    # Redirect GET requests to the home page
    return redirect(f"/")


@app.route("/suggestions")
@login_required
def suggestions():
    # Get the current user
    current_user = db.execute("SELECT * FROM Users WHERE id = ?", session["user_id"])[0]

    # Get users that share one or more personal info as
    # the current user, excluding current user and all other
    # users they follow
    # AI helped me write this query
    users = db.execute("""
        SELECT *
        FROM Users
        WHERE id != ?
        AND id NOT IN (
                SELECT following_id
                FROM Follows
                WHERE follower_id = ?
        )
        AND (
            LOWER(COALESCE(location, '')) = LOWER(COALESCE(?, ''))
            OR LOWER(COALESCE(education, '')) = LOWER(COALESCE(?, ''))
            OR LOWER(COALESCE(job, '')) = LOWER(COALESCE(?, ''))
            OR LOWER(COALESCE(relationship, '')) = LOWER(COALESCE(?, ''))
            OR LOWER(COALESCE(birthday, '')) = LOWER(COALESCE(?, ''))
        )
    """,
    session["user_id"],
    session["user_id"],
    current_user["location"],
    current_user["education"],
    current_user["job"],
    current_user["relationship"],
    current_user["birthday"])

    return render_template("suggestions.html", users=users)


@app.route("/comments/<int:post_id>", methods=["GET", "POST"])
@login_required
def comments(post_id):
    # Ensure the post exists
    post = retrieve(post_id, "Posts")
    if not post:
        return error("Post does not exist", "danger", "/")
    
    # User commented
    if request.method == "POST":
        # Get the comment content from the submitted form
        comment = request.form.get("content")

        # Ensure the comment field was submitted and is not empty
        if not comment:
            return error("Invalid operation or comments can not be empty!", "danger", f"/comments/{post_id}")
        
        # Reject comments that contain only whitespace
        if not comment.strip():
            return error("Comments can not be empty!", "danger", f"/comments/{post_id}")
        
        # Prevent comments that exceed the maximum allowed length
        if len(comment) > 1000:
            return error("Limit exceeded", "danger", f"/comments/{post_id}")
        
        # Save the new comment to the database
        db.execute("INSERT INTO Comments (post_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
                    post_id, session["user_id"], comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Notify the user that the comment was added successfully
        flash("Comment Added!", "success")
        return redirect(f"/comments/{post_id}")

    # Retrieve all comments for the current post along with the author's information
    comments = db.execute("""SELECT Comments.*, Users.username, Users.profile_picture
                           FROM Comments
                           JOIN Users ON
                           Comments.user_id = Users.id
                           WHERE post_id = ?
                           ORDER BY Comments.created_at ASC""", post_id)
    
    # Display the comments page
    return render_template("comments.html", comments=comments, post_id=post_id)


@app.route("/delete_comment", methods=["GET", "POST"])
@login_required
def delete_comment():
    # Get the ID of the post that contains the comment
    post_id = request.form.get("post_id")

    # Ensure the post exists
    post = retrieve(post_id, "Posts")
    if not post:
        return error("Post does not exist", "danger", "/")

    # User clicked on the delete button
    if request.method == "POST":
        # Get the ID of the comment to delete
        comment_id = request.form.get("comment_id")

        # Ensure the comment exists
        comment = retrieve(comment_id, "Comments")
        if not comment:
            return error("Comment does not exist", "danger", "/")
        
        # Ensure the comment belongs to the specified post
        if comment["post_id"] != post["id"]:
            return error("Invalid operation", "danger", "/")

        # Ensure the current user owns the comment
        if not comment["user_id"] == session["user_id"]:
            return error("Not authorized", "danger", "/")

        # Delete the comment
        db.execute("DELETE FROM Comments WHERE id = ?", comment_id)

        # Notify the user that the comment was deleted successfully
        flash("Comment deleted successfully!", "success")
        return redirect(f"/comments/{post_id}")
    
    # Redirect back to the comments page for non-POST requests
    return redirect(f"/comments/{post_id}")


@app.route("/edit_post", methods=["GET", "POST"])
@login_required
def edit_post():
    if request.method == "POST":
        edited = False

        # Retrieve the post to be edited
        post = retrieve(request.form.get("post_id"), "Posts")
        if not post:
            return error("Post does not exist", "danger", "/")
        
        # Get the updated post content
        new_content = request.form.get("content")

        # Ensure the current user owns the post
        if post["user_id"] != session["user_id"]:
            return error("Unauthorized.", "danger", "/")

        # Ensure the content field was submitted
        if not new_content:
            return error("Invalid operation or New Text can not be empty!", "danger", "/")

        # Reject posts containing only whitespace
        if not new_content.strip():
            flash("New Text can not be empty!", "danger")
        # Update the post content if it has changed
        elif new_content.strip() and new_content != post["content"]:
            db.execute("UPDATE Posts SET content = ? WHERE id = ?", new_content, post["id"])
            edited = True

        # Get the uploaded image, if any
        new_photo = request.files.get("post_image")

        # Remove the current image if requested
        if request.form.get("remove_image"):
            old_img = f"static/posts_pictures/{post['image']}"
            if os.path.exists(old_img):
                os.remove(old_img)
            db.execute("UPDATE Posts SET image = NULL WHERE id = ?", post["id"])
            edited = True

        # Replace the current image with a new one
        elif new_photo and new_photo.filename:
            # Make sure it's an actual image and not a malicious file
            try:
                img = Image.open(new_photo.stream)
                img.verify()

                # Reset the stream just in case the saved file is empty or corrupted.
                new_photo.stream.seek(0)
            except Exception:
                return error("Invalid image", "danger", "/")
            
            # Delete the old image if it exists
            old_img = f"static/posts_pictures/{post['image']}"
            if os.path.exists(old_img):
                os.remove(old_img)

            # Save the new image and update the database
            filename = secure_filename(new_photo.filename)
            new_photo.save(f"static/posts_pictures/{filename}")
            db.execute("UPDATE Posts SET image = ? WHERE id = ?", filename, post["id"])
            edited = True

        # Record the edit time if any changes were made
        if edited:
            db.execute("UPDATE Posts SET edited_at = ? WHERE id = ?", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), post["id"])
            flash("Post edited successfully!", "success")

        return redirect(f"/profile/{session["user_id"]}")

    # Get the post ID from the query string
    post_id = request.args.get("post_id")

    # Redirect if no post ID was provided
    if not post_id:
        return redirect("/")

    # Retrieve the requested post
    try:
        post = db.execute("SELECT * FROM Posts WHERE id = ?", request.args.get("post_id"))[0]
    except IndexError:
            return error("Post does not exist", "danger", "/")

    # Ensure the current user owns the post
    if post["user_id"] != session["user_id"]:
        return error("Unauthorized.", "danger", "/")
    
    # Display the edit post page
    return render_template("edit_post.html", post=post)


@app.route("/like", methods=["GET", "POST"])
@login_required
def like():
    # Used AI to help me use these new techniques
    # for fetching data

    is_liked = False

    # Ensure the request contains JSON data
    if not request.is_json:
        return error("Invalid operation", "danger", "/")
    
    # Get the post ID from the request body
    post_id = request.json.get("post_id")

    # Ensure a post ID was provided
    if post_id is None:
        return error("Invalid operation", "danger", "/")

    # Ensure the post ID is a valid integer
    try:
        post_id = int(post_id)
    except (ValueError, TypeError):
        return error("Invalid operation", "danger", "/")
    
    # Ensure the post exists
    if not db.execute("SELECT id FROM Posts WHERE id = ?", post_id):
        return error("Post does not exist", "danger", "/")
    
    try:
        # Like the post
        db.execute(
            "INSERT INTO Likes (user_id, post_id) VALUES (?, ?)",
            session["user_id"], post_id
        )
        is_liked = True

    except (ValueError, TypeError):
        # If the user already liked the post, unlike it instead
        db.execute(
            "DELETE FROM Likes WHERE user_id = ? AND post_id = ?",
            session["user_id"], post_id
        )
        is_liked = False

    # Get the updated number of likes for the post
    like_count = db.execute(
        "SELECT COUNT(*) AS likes_count FROM Likes WHERE post_id = ?",
        post_id
    )[0]["likes_count"]

    # Return the updated like status and like count
    return {
        "is_liked": is_liked,
        "like_count": like_count
    }


@app.route("/repost", methods=["GET", "POST"])
@login_required
def repost():
    if request.method == "POST":
        # Get the ID of the post to be shared
        post_id = request.form.get('post_id')

        # Ensure the post exists
        post = retrieve(post_id, "Posts")
        if not post:
            return error("Post does not exist", "danger", "/")
        
        try:
            # Create a repost with the optional accompanying text
            db.execute("INSERT INTO Reposts (post_id, user_id, text, created_at) VALUES (?, ?, ?, ?)",
                            post_id, session['user_id'], request.form.get('text'), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except ValueError:
            # Prevent users from reposting the same post more than once
            return error("You have already shared this post", "danger", "/")
            
        # Notify the user that the repost was successful
        flash("Post shared successfully!", "success")
        return redirect("/")
    
    # Display the repost page if a valid post ID is provided
    if request.args.get('post_id'):
        return render_template("repost.html", post_id=request.args.get('post_id'))
    else:
        # Reject invalid requests without a post ID
        return error("Invalid operation", "danger", "/")