CREATE TABLE ingredients (ingredient_id INTEGER NOT NULL, ingredient TEXT NOT NULL, FOREIGN KEY(ingredient_id) REFERENCES titles(id));
CREATE TABLE ingredients (
	ingredients_id INTEGER, 
	ingredient TEXT NOT NULL, 
	FOREIGN KEY(ingredient_id) REFERENCS titles(id)
);


CREATE TABLE titles (
	id INTEGER,
	title TEXT NOT NULL,
	url, TEXT NOT NULL,
	PRIMARY KEY(id)
);


CREATE TABLE users (
	id INTEGER
	username TEXT NOT NULL,
	hash TEXT NOT NULL,
);
