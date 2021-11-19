from functools import wraps

from flask import redirect, render_template, session


def login_required(f):
    """
    this decorator function is provided by flask. it checks to see if the user is signed in.
    if not, the user is sent to the login page.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("name") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def report_error(message):
    """
    Sends an error message (passed from app.py) to the user
    """

    # TODO create a modal using bootstrap to update error.html (or maybe layout.html?) to be a bit more UX friendly
    return render_template("error.html", message=message)
