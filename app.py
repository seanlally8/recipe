import re
from tempfile import mkdtemp

import cv2
import requests
from bs4 import BeautifulSoup
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from random_word import RandomWords
from sqlalchemy import (Column, ForeignKey, Integer, MetaData, String, Table,
                        and_, create_engine, insert, select)
from werkzeug.security import check_password_hash, generate_password_hash

from app_model import grab_title_id, insert_title, update_tables
from buttress import (check_extension, extract_strings, html_to_string,
                      image_preprocessing, login_required, parse_image,
                      report_error)

# Initate and configure flask app
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = mkdtemp()
Session(app)

# Initiate metadata object so we can create Table objects to manipulate our data
metadata = MetaData()

# Create the table objects (corresponding to recipe.db)
ingredients = Table("ingredients", metadata,
                    Column("title_id", Integer(), ForeignKey("titles.id")),
                    Column("ingredient", String(), nullable=False)
                    )

instructions = Table("instructions", metadata,
                     Column("title_id", Integer(), ForeignKey("titles.id")),
                     #Column("instruction_title", String()),
                     Column("instruction", String(), nullable=False)
                     )

recipe_books = Table("recipe_books", metadata,
                     Column("title_id", Integer(), ForeignKey("titles.id")),
                     Column("user_id", Integer(), ForeignKey("users.id"))
                     )

titles = Table("titles", metadata,
               Column("id", Integer(), primary_key=True),
               Column("title", String(), nullable=False),
               Column("url", String())
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
    The user can enter a url containing a recipe in order to
    add it to their 'Library'
    """

    # If user arrives via GET, load the homepage
    # which contains an input field for recipe urls
    if request.method == "GET":
        return render_template("index.html")

    # If user submits forms on homepage,
    # produce entry in recipe book
    if request.method == "POST":

        # Check to make sure the user actually sent a url when they hit the 'Log a recipe' button
        url = request.form.get("url")
        if not url and "image" not in request.files:
            return report_error("no url sent.")

        # if url was entered, parse the html of the given page and update database to include
        # recipe data
        if request.form.get("url"):

            # Check for proper url format. This section might benefit from some regular expression magic.
            if not url.startswith("http"):
                return report_error("not a url")

            # Fetch contents of url
            load = requests.get(url)

            # Create an object containing the html Document Object Model (DOM) from the url entered above
            soup = BeautifulSoup(load.text, "lxml")

            # Grab the recipe title from the DOM
            recipe_title = soup.select("h1.c-recipe-details-header__title")[0].string.strip()

            # Grab the ingredients list from the DOM
            # html_to_string converts the list elements to bare strings (see buttress.py)
            ingredients_data = html_to_string(soup.select("ol > li"))

            # Grab the instruction_titles from the DOM
            #instructions_title = html_to_string(soup.select("div.c-recipe-step__title.c-heading.c-heading--brand-7"))

            # Grab the actual instructions from the DOM
            instructions_body = html_to_string(soup.select("div.col-12 > p"))

            # Check to make sure the last 3 'grabs' returned some value
            if not recipe_title or not ingredients_data or not instructions_body:
                return report_error("Unable to locate the required ingredients at the given url")

            # Attempt to fetch the url, provided by the user, from the database
            stmt = select(titles.c.url).where(titles.c.url == url)
            urls = connection.execute(stmt).fetchall()

            # If the url isn't in the database, update titles table, ingredients table and instructions table,
            # This condition ensures that we don't duplicate recipes in the database.
            if not len(urls):
                update_tables(recipe_title, instructions_body, ingredients_data, url)
                return redirect("/recipebook")
            # If the url IS in the database, check to see if it's in the user's library
            # i.e., a place in the db where the recipe title is associated with the user 

            # To do this, we first grab the title_id
            title_id = grab_title_id(recipe_title)

            # Then, with the title_id, we attempt to select the recipe title from this user's library
            recipe_check = select(recipe_books).where(and_(recipe_books.c.title_id == title_id,
                                                        recipe_books.c.user_id == session["user_id"]))
            recipe_check = connection.execute(recipe_check).fetchall()

            # If the recipe isn't in their library, we add it
            if not recipe_check:
                insert_title(title_id)
                return redirect("/recipebook")

            # If the recipe is in the library, return an error message telling the user they already have it.
            return report_error("you already have that recipe in your library")

        # If an image file was submitted, process the image with opencv, convert
        # the image to string using Optical Character Recognition (OCR)/pytesseract, then add
        # the recipe to the database
        elif request.files["image"]:

            # Fetch the image from the "post" request
            image = request.files["image"]

            # Extract extension
            ext = image.filename.rsplit(".")[1].lower()

            # Check for valid extension (.jpg or .png)
            check_extension(ext)

            # Save the image to filesystem
            img = image.save(f"tmpimage.{ext}")

            # Read the file into memory so we can manipulate the image with code
            filename = f"tmpimage.{ext}"
            img = cv2.imread(filename)

            # Prepare the image for OCR text recognition
            processed_image = image_preprocessing(img)

            # Create a list of image arrays, each containing a separate chunk of text
            # from the original image
            image_arrays = parse_image(processed_image)

            # Produce a list of strings containing
            # the OCRed text from each image
            recipe_strings = extract_strings(image_arrays)

            # Remove the jpeg files generated by image.save and parse_image
            #remove_files()

            # Check to make sure the "extract_strings" function returns something
            if not len(recipe_strings):
                return report_error("Highly uncertain about that image. Resubmit material, glareless and straight.")

            # Split ingredients and instruction into smaller units, so we can more
            # easily manipulate the data on the front-end
            ingredients_list = []
            list_of_ingredients = []
            for recipe_str in recipe_strings:
                if "prepare" in recipe_str.lower() or "preheat" in recipe_str.lower() or "assemble" in recipe_str.lower() or "bowls" in recipe_str.lower():
                    list_of_instructions = re.split(r"\n\n", recipe_str)
                    print(1)
                    print(list_of_instructions)
                if "\u00BC" in recipe_str.lower() or "\u00BD" in recipe_str.lower():
                    ingredients_list = re.split(r"\n", recipe_str)
                    print(2)
                    print(ingredients_list)

            # Check to make sure you got both instructions and ingredients
            if not ingredients_list or not list_of_instructions:
                return report_error("Highly uncertain about that image. Resubmit material, glareless and straight.")

            # Clean ingredients list (specifically delete empty strings)
            for item in ingredients_list:
                if not item:
                    ingredients_list.remove(item)

            # TEMPORARY -- assign a random word to be our recipe title until we figure out how to get the actual title
            r = RandomWords()
            random_title = r.get_random_word()

            # Update tables with recipe data gleaned via OCR
            update_tables(random_title, list_of_instructions, ingredients_list, None)

            # Fetch the autogenerated title_id so we can add the recipe to the user's 'library'
            # i.e. a place in the database where the title is associated with the user
            title_id = grab_title_id(random_title)

            # Insert the title into their 'library'
            insert_title(title_id)

            # Send user to their 'book o recipes' (the front end of their 'library')
            return redirect("/recipebook")

        # If we've made it this far then the user hit the upload button without
        # attaching an image.
        return report_error("no image sent.")



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

            return redirect("/recipebook")


@app.route("/logout")
def logout():
    """
    Log the user out and send them to the login page
    """

    session.clear()

    return redirect("/")


@app.route("/recipebook", methods=["GET", "POST"])
@login_required
def recipebook():
    """
    Recipe book provides the user with a select menu containing all their recipes.
    When they select one and press the "let's cook!" button,
    a screen appears displaying the desired recipe.
    """

    # If user arrives via GET (that is, if they've clicked on "Library")
    # display a select menu with all their recipes
    if request.method == "GET":

        # Fetch the user's recipe titles to populate the select menu
        stmt = select(titles.c.title).where(titles.c.id.in_(select(recipe_books.c.title_id).where(
                                                                   recipe_books.c.user_id == session["user_id"]))).order_by(titles.c.title)
        recipe_titles = connection.execute(stmt).fetchall()

        # Capture the number of titles returned by the above query.
        # We can use this to set a max size of the select menu
        # before it overflows and becomes scrollable.
        titles_list_length = len(recipe_titles)

        return render_template("recipebook.html", recipe_titles=recipe_titles, titles_list_length=titles_list_length)

    # If user submits post request (i.e. if they select a recipe to open),
    # return a page with the desired recipe
    if request.method == "POST":

        # Retrieve the ingredients and instructions for the given recipe title
        recipe_title = request.form.get("title")
        stmt = select(ingredients.c.ingredient).where(ingredients.c.title_id.in_(select(titles.c.id).where(
                                                                                 titles.c.title == recipe_title)))
        recipe_ingredients = connection.execute(stmt).fetchall()

        #stmt = select(instructions.c.instruction_title).where(instructions.c.title_id.in_(
                                                              #select(titles.c.id).where(
                                                                    #titles.c.title == recipe_title)))
        #recipe_instruction_title = connection.execute(stmt).fetchall()

        stmt = select(instructions.c.instruction).where(instructions.c.title_id.in_(select(titles.c.id).where(
                                                                                    titles.c.title == recipe_title)))
        recipe_instruction = connection.execute(stmt).fetchall()

        stmt = select(titles.c.url).where(titles.c.title == recipe_title)
        recipe_url = connection.execute(stmt).fetchone()

        # Pass the retrieved data into the recipe.html template and return that page. The user will now have a page
        # containing a clear readable recipe from their book o' recipes.
        return render_template("recipe.html", recipe_title=recipe_title, recipe_ingredients=recipe_ingredients,
                               instructions=recipe_instruction,
                               recipe_url=recipe_url)



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


@app.route("/shoppinglist")
def shoppinglist():
    """
    Where the user can make a shopping list
    """

    return render_template("shoppinglist.html")
