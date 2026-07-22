# ConnectHub
#### Video Demo:  https://youtu.be/ALi1FHPLoJg?si=pyZAAPVSm1ePdy1p
#### Description:
ConnectHub is a social networking web application inspired by Facebook. 
The application allows users to create accounts, interact with other users, publish posts, and engage with content through likes, comments, reposts, and follows.

The project was built using Flask as the backend framework, SQLite as the database, Jinja templates for rendering HTML pages, Bootstrap for responsive design, and JavaScript to improve the user experience with dynamic interactions.

## Features

### Authentication

- Register a new account
- Passwords securely hashed using Werkzeug
- Log in and log out
- Change password
- Session management using Flask

### User Profiles

Each user has a personal profile containing:

- Username
- Biography
- Profile picture
- Join date
- Number of followers
- Number of following
- Number of posts

Users can edit their profile information at any time.

### Posts

Users can:

- Create text posts
- Upload an optional image with each post
- Server-side image validation before uploads are accepted
- Edit their own posts
- Delete their own posts
- View timestamps
- See edited indicators when a post has been modified


### Social Features

Users can interact with one another by:

- Following users
- Unfollowing users
- Liking posts
- Removing likes
- Commenting on posts
- Reposting posts
- Searching for other users

The home feed displays posts created by the current user as well as users they follow, ordered by the newest first.

### User Experience

Several quality-of-life improvements were implemented:

- Responsive layout for desktop and mobile devices
- Auto-expanding text areas
- Empty-state messages when no content exists


### Technologies Used

**Backend:**
- Python
- Flask
- SQLite
- CS50 SQL Library

**Frontend:**
- HTML
- CSS
- Bootstrap 5
- JavaScript
- Jinja2 Templates

**Other Libraries:**
- Werkzeug (password hashing and secure filenames)
- Pillow (image validation)

## Database Design

The application stores data using SQLite.

The main tables are:

- **Users:** – account information and profile data
- **Posts:** – user posts and attached images
- **Comments:** – comments on posts
- **Likes:** – stores which users liked which posts
- **Follows:** – follower relationships between users
- **Reposts:** – reposted content

## How to Run

1. Clone the repository.

https://github.com/ZiadAhmed2125/ConnectHub.git

2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Run the Flask application:

```bash
flask run
```

4. Open your browser and visit:

```text
http://127.0.0.1:5000
```

## How to Use

After launching the application, users can register for a new account by providing a unique username and password. Existing users can log in using their username and password. Once authenticated, users gain access to all of ConnectHub's features.

After logging in for the first time, users can personalize their profile by uploading a profile picture and writing a short biography. Each profile displays the user's username, join date, number of posts, followers, and following, providing an overview of their activity on the platform. Based on profile information such as location, education, and occupation, ConnectHub also suggests other users they may be interested in following.

The home page serves as the main feed, displaying posts created by the logged-in user as well as users they follow. Posts are ordered from newest to oldest.

Users can create new posts by writing text and optionally attaching an image. Uploaded images are validated on the server before being stored. Once published, posts immediately become visible in the appropriate feeds. Users may edit or delete only their own posts, while edited posts display an indicator showing that they have been modified.

Each post supports multiple forms of interaction. Users can like or unlike posts, leave comments, and repost content to share it with their followers. These interactions update the application's database and are reflected throughout the interface.

Users can search for other accounts by username and visit their public profiles. From a user's profile page, visitors can browse that user's posts and choose to follow or unfollow them. Following another user causes all their posts and future ones to appear in the follower's home feed.

The application includes several quality-of-life features designed to improve usability. Text areas automatically expand while typing, the interface adapts to different screen sizes using responsive design, and informative messages are displayed whenever a page has no content to show, such as when a user has no posts or is not following anyone.

Users may update their profile information or change their password at any time through the account settings. When they have finished using the application, they can securely log out, ending their authenticated session.


## What I Learned

This project brought together nearly every major topic covered in CS50x, including Python, Flask, SQL, HTML, CSS, JavaScript, authentication, file handling, responsive web design, and database design.

Building ConnectHub taught me how to handle a large-scale software project. As the application expanded, I gained experience organizing a growing codebase, managing interactions between multiple technologies, and testing and debugging features. This project helped me understand the importance of planning, modularity, and maintainability when developing such large projects.

ConnectHub is the largest and most comprehensive project I have built so far, and it represents the culmination of everything I learned throughout CS50x.

## Design Decisions

The following design decisions were made during development to improve the application's maintainability, performance, and security.

- Database Simplicity:
SQLite was selected because it is lightweight, requires no separate server, and integrates well with Flask. For a project of this scale, it provides all necessary functionality while keeping deployment straightforward.

- The application uses a normalized SQLite database where likes, comments, follows, and reposts are stored in separate tables rather than inside the Users or Posts tables. This simplifies querying,  and 
avoids duplicated data.

- Bootstrap was used for the responsive layout, while custom CSS was added to create a social-media-inspired interface.

- Feed Generation:
Rather than storing a pre-generated feed for every user, the home feed is generated dynamically using SQL joins and subqueries. This ensures users always see the latest posts from themselves and the people they follow without needing additional synchronization logic.

- User input is validated on both the client and server sides whenever appropriate. Invalid actions are handled gracefully using Flask flash messages and redirects instead of exposing raw errors to the user.
