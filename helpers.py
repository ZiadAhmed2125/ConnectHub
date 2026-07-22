from cs50 import SQL

from flask import redirect, render_template, session, flash
from functools import wraps

# Connect to the SQLite database
db = SQL("sqlite:///fb.db")


def login_required(f):
    """
    Decorator that restricts access to authenticated users.
    Redirects unauthenticated users to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is logged in
        if session.get("user_id") is None:
            return redirect("/login")

        # Continue to the requested route
        return f(*args, **kwargs)

    return decorated_function


def error(err_msg, category, url):
    """
    Flash an error (or status) message and redirect the user.

    Parameters:
        err_msg (str): Message to display.
        type (str): Bootstrap flash category (e.g., "danger", "success").
        url (str): URL to redirect to.
    """
    flash(err_msg, category)
    return redirect(url)


def retrieve(id, table):
    """
    Retrieve a single row from a database table by its ID.

    Returns:
        dict: The matching row.
        None: If no row with the given ID exists.
    """
    try:
        return db.execute(f"SELECT * FROM {table} WHERE id = ?", id)[0]
    except IndexError:
        return None


def is_int(entry):
    """
    Check whether a value can be converted to an integer.

    Returns:
        bool: True if conversion succeeds, False otherwise.
    """
    try:
        int(entry)
        return True
    except (ValueError, TypeError):
        return False