# recipe
(This Readme is under construction)

Recipe is a web app for making shopping lists and collecting recipes. It provides 3 basic services:

1. Converts html and scanned pages to virtually editable scrapbook recipes
2. Allows user to organize recipes using tags
3. Produces a shopping list -- without duplicate ingredients -- given a a group of recipes 

These are the core services upon which I hope to build a broader repertoire. Specifically, I would like to allow the user to submit the shopping list to instacart with the click of a button.

The following will, I hope, explain in greater depth how each service works from a user's perspective. I will also dive into the nitty gritty of the python (controller) code, outlining the structure of the program and justifying some of my design choices. We'll use the following structure as our guide:

-- The User Experience --
1. Logging a recipe
2. Organizing Your library
3. Making a Shopping List

-- The Code --
1. app.py
1. buttress.py
1. app_model.py

-- Looking Ahead --
1. Rewriting SQL (decluttering code)
1. Training OCR Data
1. Integrating Instacart (or similar third-party app)

To be continued....

---

This app is being developed as the final project for <a href="https://cs50.harvard.edu/x/2021/">Harvard's CS50</a>, taught by David Malan. It is currently in its early phases, but I will be updating this readme as I get closer to completion.

To Dos
- [ ] buttress.py line 25 create a modal using bootstrap to update error.html (or maybe layout.html?) to be a bit more UX friendly
- [ ] Rewrite sql code as orm?
- [ ] Organize OCR strings using the number (e.g. "1.", "2.") that commences each instruction
- [ ] For OCR strings, delete everything after the exclamation point (this is specific to purple carrot recipes
- [ ] 

