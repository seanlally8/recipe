from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, create_engine


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

