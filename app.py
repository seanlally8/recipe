from tempfile import mkdtemp

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import (Column, ForeignKey, Integer, MetaData, String, Table,
                        create_engine)
from werkzeug.security import generate_password_hash

from assist import login_required, report_error

# Initate and configure flask app
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = mkdtemp()
Session(app)

# Initiate metadata object so we can create Table objects to manipulate our data
metadata = MetaData()

# Create the table objects (corresponding recipe.db)
ingredients = Table("ingredients", metadata, 
    Column("ingredients_id", Integer(), ForeignKey("titles.id")),
    Column("ingredient", String(), nullable=False)
)

titles = Table("titles", metadata,
    Column("id", Integer(), primary_key=True),
    Column("title", String(), nullable=False),
    Column("url", String(), nullable=False)
)

users = Table("users", metadata,
    Column("id", Integer(), primary_key=True),
    Column("username", String(), nullable=False),
    Column("passhash", String(), nullable=False),
)

recipe_books = Table("recipe_books", metadata,
    Column("title_id", Integer(), ForeignKey("titles.id")),
    Column("user_id", Integer(), ForeignKey("users.id"))
)

# Initiate SQLAlchemy Engine
engine = create_engine("sqlite:///recipe.db", echo=True, future=True)

# Create tables (if not created)
metadata.create_all(engine)


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

        # Create a hash for the given password, to ensure we don't have access to the user's password
        passhash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16) 

        # Insert username and hash into users table
        ins = users.insert().values(
                username=username,
                passhash=passhash
        )

        print(str(ins))

        # Check to see whether they've given a username and password
        if not username: 
            report_error("please provide a username")

        if not password:
            report_error("please provide a password")

