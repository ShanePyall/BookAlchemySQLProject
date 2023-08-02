from datetime import date
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os

# Creates path to sql database that's stored in the server
file_path = os.path.abspath(os.getcwd()) + "\\library.sqlite"
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + file_path
db = SQLAlchemy()
db.init_app(app)


class Author(db.Model):
    # Creates an Author object
    __tablename__ = "authors"

    author_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    birth_date = db.Column(db.Date)
    date_of_death = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f"""\"{self.name}\"
    Date of birth: {self.birth_date}
    Date of death: {self.date_of_death}
    Advanced(DB ID): {self.author_id}"""


class Book(db.Model):
    # Creates a Book object
    __tablename__ = "books"

    book_id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.Integer)
    title = db.Column(db.String)
    publication_year = db.Column(db.Date)
    author_id = db.Column(db.Integer)  # Foreign Key

    def __repr__(self):
        return f"""\"{self.title}\"
    ISBN number: {self.isbn}
    Year published: {self.publication_year}
    Author: {self.author_id}"""


def html_date_comprehension(data):
    # Translates raw HTML date data, to desired type for storing in our database.
    data_list = data.split('-')
    res = date(int(data_list[0]),
               int(data_list[1]),
               int(data_list[2]))
    return res


@app.route("/add_author", methods=['GET', 'POST'])
def add_author():
    """Creates new author obj and stores in our database"""
    # Receives: name and birthdate as minimum requirement.
    if request.method == 'POST':
        name = request.form.get("name")
        birth_date = request.form.get("birthdate")
        date_of_death = request.form.get("date_of_death", '')

        if date_of_death == '':
            death_res = None
        else:
            death_res = html_date_comprehension(date_of_death)
        birth_res = html_date_comprehension(birth_date)

        # Creates data as an Author obj.
        res = Author(name=name,
                     birth_date=birth_res,
                     date_of_death=death_res)

        # Stores new author in database.
        db.session.add(res)
        db.session.commit()
        return home()
    # If request is 'GET', render add author template
    return render_template("add_author.html")


@app.route("/add_book", methods=['GET', 'POST'])
def add_book():
    """Creates new book obj and stores in database"""
    if request.method == 'POST':
        received_author = request.form.get("name")
        res = Author.query.all()
        authors_present = [author.name for author in res]
        # If author not present in our database, show error.
        if received_author not in authors_present:
            e = ["Please create the author before the book"]
            return error(500, message=e)

        # Locate author to tie id in books table, creating foreign key link
        authors_id = [author.author_id for author in res
                      if author.name == received_author]
        isbn = request.form.get("isbn")
        publication_year = request.form.get("publication_year")
        title = request.form.get("title")

        # Create Book obj with received data
        publication_year_res = html_date_comprehension(publication_year)
        db.session.add(Book(author_id=authors_id[0], isbn=isbn,
                            publication_year=publication_year_res,
                            title=title))

        # Store new book in database
        db.session.commit()
        return home()
    # If request is 'GET', render add book template
    return render_template("add_book.html")


@app.route("/home", methods=['GET', 'POST'])
def home():
    """Displays all books present in database"""
    if request.method == 'POST':
        search = request.form.get("Search")
        titles = request.form.get("Titles A-Z")
        authors = request.form.get("Authors A-Z")
        # If user has entered data in the search field.
        if search is not None:
            books_and_authors = Book.query.join(Author, Author.author_id == Book.author_id) \
                .add_columns(Book.title, Author.name, Book.book_id)\
                .where(Book.title.contains(search)).all()
            # If the search data was not a substring, return apology message.
            if not books_and_authors:
                return error(e=404, message=['Sorry, no books matched with what you entered'])
        # Check if titles button was pressed, return titles ordered A-Z.
        elif titles is not None:
            books_and_authors = Book.query.join(Author, Author.author_id == Book.author_id)\
                .add_columns(Book.title, Author.name, Book.book_id).order_by(Book.title).all()
        # Check if authors button was pressed, return authors ordered A-Z.
        elif authors is not None:
            books_and_authors = Book.query.join(Author, Author.author_id == Book.author_id)\
                .add_columns(Book.title, Author.name, Book.book_id).order_by(Author.name).all()
        # Safety net: if a post request was sent but no data was received, send defualt list.
        else:
            books_and_authors = Book.query.join(Author, Author.author_id == Book.author_id)\
                .add_columns(Book.title, Author.name, Book.book_id).all()
    # Send default list
    else:
        books_and_authors = Book.query.join(Author, Author.author_id == Book.author_id)\
            .add_columns(Book.title, Author.name, Book.book_id).all()
    return render_template("home.html", books=books_and_authors)


@app.route("/book/<int:book_id>/delete", methods=['POST'])
def delete(book_id):
    """Deletes book obj from database"""
    # recieves book_id from route, finds and returns list of results in database.
    target = Book.query.filter_by(book_id=book_id).all()
    db.session.delete(target[0])
    db.session.commit()
    return error(e=500, message=['Delete successful!'])


@app.errorhandler(404)
def error(e, message=None):
    """mainly used for errors, can be used for statments and returning to home"""
    if message is None:
        message = ["Site not found"]
    print(f"Error code: {e}")
    return render_template("404.html", message=message)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
