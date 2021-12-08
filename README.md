# recipe
(This Readme is under construction)

Developed as the final project for <a href="https://cs50.harvard.edu/x/2021/">Harvard's CS50</a>, recipe is a web app for making shopping lists and collecting recipes. It provides 3 basic services:

- Converts html and scanned pages to virtually editable scrapbook recipes
- Allows user to organize recipes using tags
- Produces a shopping list -- without duplicate ingredients -- given a a group of recipes 

These are the core services upon which I hope to build a broader repertoire. Specifically, I would like to allow the user to submit the shopping list to instacart with the click of a button.

The following will explain in greater depth how each service works from a user's perspective. I will also dive into the nitty gritty of the python (controller) code, outlining the structure of the program and justifying some of my design choices. We'll use the following structure as our guide:


1. [Logging a recipe](#logging-a-recipe)
1. [Organizing Your library](#organizing-your-library)
1. [Making a Shopping List](#making-a-shopping-list)
3. [app.py](#app)
4. [buttress.py](#buttress)
5. [app_model.py](#app_model)
6. [Rewriting SQL](#rewriting-sql)
7. [Training OCR Data](#training-ocr-data)
8. [Integrating Instacart](#integrating-instacart)


# Logging a Recipe


# Organizing Your library


# Making a Shopping List


# App


# Buttress


# App_Model



# Rewriting SQL


# Training OCR Data


# Integrating Instacart



To Dos
- [ ] buttress.py line 25 create a modal using bootstrap to update error.html (or maybe layout.html?) to be a bit more UX friendly
- [ ] Rewrite sql code as orm?
- [ ] Organize OCR strings using the number (e.g. "1.", "2.") that commences each instruction
- [ ] For OCR strings, delete everything after the exclamation point (this is specific to purple carrot recipes
- [ ] 

