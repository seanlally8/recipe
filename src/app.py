from flask import Flask, flash, redirect, render_template, request, session
from assist import login_required
from flask_session import Session
from tempfile import mkdtemp

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = mkdtemp()
Session(app)

@app.route("/")
@login_required
def index():
    return render_template("index.html") 

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Route via which user will login to their Recipe account
    """
   
    # If user arrives via GET, simply load the page containing the login forms.
    if request.method == "GET":
        return render_template("login.html") 

    # If they've arrived via POST, then they've submitted their username and password, which
    # this conditional will process
    if request.method == "POST":  

        # Store username and password in variables for ease of coding
        username = request.form.get("username")
        password = request.form.get("password")

        # Check to see whether they've given a username and password
        if not username:
            return render_template("error.html", username=username) # error.html should include modal popup with the error message.
        
        if not password:
            return render_template("error.html", password=password)
