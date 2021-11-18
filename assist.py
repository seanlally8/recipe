from functools import wraps

from flask import g, redirect, render_template, request, session, url_for


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
           return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def report_error(message):
    return render_template("error.html", message=message)

