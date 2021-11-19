from tempfile import mkdtemp

import requests
from bs4 import BeautifulSoup
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import (Column, ForeignKey, Integer, MetaData, String, Table,
                        and_, create_engine, insert, select)
from werkzeug.security import check_password_hash, generate_password_hash

from buttress import login_required, report_error

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
                    Column("title_id", Integer(), ForeignKey("titles.id")),
                    Column("ingredient", String(), nullable=False)
                    )

instructions = Table("instructions", metadata,
                     Column("title_id", Integer(), ForeignKey("titles.id")),
                     Column("instruction_title", String()),
                     Column("instruction", String(), nullable=False)
                     )

recipe_books = Table("recipe_books", metadata,
                     Column("title_id", Integer(), ForeignKey("titles.id")),
                     Column("user_id", Integer(), ForeignKey("users.id"))
                     )

titles = Table("titles", metadata,
               Column("id", Integer(), primary_key=True),
               Column("title", String(), nullable=False),
               Column("url", String(), nullable=False, unique=True)
               )

users = Table("users", metadata,
              Column("id", Integer(), primary_key=True),
              Column("username", String(), nullable=False, unique=True),
              Column("passhash", String(), nullable=False),
              )

# Initiate SQLAlchemy Engine
engine = create_engine("sqlite:///recipe.db?check_same_thread=False", echo=True, future=True)

# Create a connection object so we can execute commands/queries on the database.
connection = engine.connect()

# Create tables (if not created)
metadata.create_all(engine)


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """
    here, the user can enter a url containing a recipe in order to
    add it to their 'Book o' Recipes'
    """

    # If user arrives via GET, load the homepage
    # which contains an input field for recipe urls
    if request.method == "GET":
        return render_template("index.html")

    # If user submits forms on homepage,
    # produce entry in recipe book
    if request.method == "POST":

        # Store recipe url provided by user in
        # variable for readability and ease of coding
        url = request.form.get("url")

        # Check for proper url format. This section might benefit from some regular expression magic.
        if not url.startswith("http"):
            return report_error("not a url")

        # Fetch contents of url
        load = requests.get(url)

        # Create an object containing the html Document Object Model (DOM) from the url entered above
        soup = BeautifulSoup(load.text, "lxml")

        # Grab the recipe title from the DOM
        recipe_title = soup.select("h1.c-recipe-details-header__title")

        # Grab the ingredients list from the DOM
        ingredients_data = soup.select("ol > li")

        # Grab the instructions from the DOM
        instructions_title = soup.select("div.c-recipe-step__title.c-heading.c-heading--brand-7")
        instructions_body = soup.select("div.col-12 > p")

        # Check to make sure the previous methods returned some value
        if recipe_title is None or ingredients_data is None or instructions_title is None or instructions_body is None:
            return report_error("Unable to locate the required ingredients at the given url")

        # TODO write a condition to see if that url already exists in the database == maybe even right after url is defined above?
        stmt = select(titles.c.url).where(titles.c.url == url)
        urls = connection.execute(stmt).fetchall()
        
        
        # Update titles table, ingredients table and instructions table, as long as that url doesn't already exist
        # This condition ensures that we don't duplicate recipes in the database.
        if len(urls) != 1:
            stmt = insert(titles).values(title=recipe_title[0].string.strip(), url=url)
            connection.execute(stmt)
            connection.commit()

            # Grab the title id from the titles table so we can plug it in as a Foreign Key in other tables
            stmt = select(titles.c.id).where(titles.c.url == url)
            title_id = connection.execute(stmt).fetchall()
            title_id = title_id[0].id

            # Insert ingredients into ingredients table.
            for ingredient in ingredients_data:

                # Stop at Salt, since everything after Salt is unnecessary information.
                if ingredient.string.strip().startswith("Salt"):
                    break
                stmt = insert(ingredients).values(ingredient=ingredient.string.strip(), title_id=title_id)
                connection.execute(stmt)
            connection.commit()

            # Insert instructions into instructions table
            for (entry, title) in zip(instructions_body, instructions_title):
                stmt = insert(instructions).values(instruction=entry.string.strip(),
                                                   instruction_title=title.string.strip(),
                                                   title_id=title_id)
                connection.execute(stmt)
            connection.commit() 

        # Update the "recipe_books" table to link the recipe with the user
        # First, get the title id TODO write a function in data model or buttress that just fetches the title_id
        stmt = select(titles.c.id).where(titles.c.url == url)
        title_id = connection.execute(stmt).fetchall()
        title_id = title_id[0].id

        # Now insert the data TODO You should also check to make sure the user doesn't already have the recipe in their book
        stmt = insert(recipe_books).values(user_id=session["user_id"], title_id=title_id) 
        connection.execute(stmt)
        connection.commit()

        return redirect("/recipebook")


@app.route("/recipebook")
@login_required
def recipebook():
    return render_template("recipebook.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Route via which user will login to their Recipe account
    """

    # Clear the session, so a new session can be created
    session.clear()

    # If user arrives via GET, simply load the page containing the login forms.
    if request.method == "GET":
        return render_template("login.html")

    # If they've arrived via POST, then they've submitted their
    # username and password, which this conditional will process
    elif request.method == "POST":

        # Store username and password in variables for readability
        username = request.form.get("username")
        password = request.form.get("password")

        # Check to see whether they've given a username and password
        if not username:
            return report_error("please provide a username")
        if not password:
            return report_error("please provide a password")

        # Check to see if the username/password pair are in the users table
        sel = select(users).where(and_(users.c.username == username))
        user_account = connection.execute(sel).fetchall()

        # If they're not in the table, tell the user as much
        if len(user_account) != 1 or not check_password_hash(user_account[0]["passhash"], password):
            return report_error("username and/or password does not exist")
        elif len(user_account) == 1:
            session["user_id"] = user_account[0].id

            return redirect("/")


@app.route("/logout")
def logout():
    """
    Log the user out and send them to the login page
    """

    session.clear()

    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Route via which the user can register for a new account
    """

    # If user arrives via GET, show them the forms needed to register
    if request.method == "GET":
        return render_template("register.html")

    # If arrived via POST, process the information submitted by the user
    elif request.method == "POST":

        # Store user input in variables for readability and ease of coding
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Generate a hash for the password
        passhash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        # Check to make sure they've provided input in each field
        if not username:
            return report_error("you didn't provide a username")
        elif not password:
            return report_error("you didn't provide a password")
        elif not confirmation:
            return report_error("you didn't confirm your password")

        # If the password doesn't match the password confirmation, let the user know
        elif password != confirmation:
            return report_error("passwords don't match")

        # Check to make sure the username doesn't exist
        sel = select([users.c.username]).where(users.c.username == username)
        rp = connection.execute(sel)
        user_account = rp.fetchall()

        # If the username exists, let the user know so they can try again
        if len(user_account) == 1:
            return report_error("username already exists")

        # Create a record for username and hash in users table
        ins = insert(users).values(
                username=username,
                passhash=passhash
        )
        rp = connection.execute(ins)
        connection.commit()
        
        # Fetch the user's id number from the data base so we can use it later and log the sessionr
        stmt = select(users.c.id).where(username == username)
        user_id = connection.execute(stmt).fetchall()
        

        # Log the username in the session
        session["user_id"] = user_id[0].id

        return redirect("/")
