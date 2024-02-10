from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key = 'your_secret_key'

password = '12345'
owner_name = 'postgres'
database_name = 'postgres'
DATABASE_URL = 'postgresql://'+ owner_name +':'+ password +'@localhost/' + database_name
print('database:', DATABASE_URL)

engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))
print('Database set up')

with engine.connect() as eng:
    for row in eng.execute("select * from books limit 1 offset 1;"):
        print(row)



users = {}

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('secure'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Query the database to check if the username and password match
        user = db.execute("SELECT username FROM users WHERE username = :username AND password = :password", {"username": username, "password": password}).fetchone()
        if user:
            # Authentication successful, set session and redirect to secure page
            session['username'] = username
            flash('Login successful.', 'success')
            return redirect(url_for('secure'))
        else:
            # Authentication failed, display error message
            error = 'Invalid username or password'

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists in the database
        existing_user = db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).fetchone()
        if existing_user:
            error = 'Username already taken, please choose another'
        else:
            # Insert new user into the database
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": username, "password": password})
            db.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', error=error)



@app.route('/secure')
def secure():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Execute SQL query
    book_row = None
    with engine.connect() as connection:
        book_row = connection.execute("SELECT * FROM books LIMIT 1 OFFSET 1;").fetchone()
    return render_template('secure.html', username=session['username'], book_row=book_row)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/search')
def search():
    query = request.args.get('query')
    if query:
        query = f"%{query}%"
        sql_query = text("SELECT * FROM books WHERE isbn ILIKE :query OR title ILIKE :query OR author ILIKE :query")
        results = db.execute(sql_query, {"query": query}).fetchall()
        return render_template('search_results.html', results=results)
    return redirect(url_for('secure'))


@app.route('/book/<isbn>', methods=['GET', 'POST'])
def book(isbn):
    # Retrieve book information
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    # Retrieve existing reviews for the book
    reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()

    # Check if the current user has already submitted a review for this book
    review_exists = False
    if 'username' in session:
        username = session['username']
        review_exists = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND username = :username", {"isbn": isbn, "username": username}).fetchone()

    return render_template('book.html', book=book, reviews=reviews, review_exists=review_exists)


@app.route('/submit_review/<isbn>', methods=['POST'])
def submit_review(isbn):
    if request.method == 'POST':
        # Get username from session
        username = session.get('username')

        # Check if the user has already submitted a review for this ISBN
        existing_review = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND username = :username", {"isbn": isbn, "username": username}).fetchone()
        if existing_review:
            flash('You have already submitted a review for this book.', 'warning')
            return redirect(url_for('book', isbn=isbn))

        # If not, proceed with submitting the new review
        comment = request.form['comment']
        rating = request.form['rating']

        # Save the review to the database
        db.execute("INSERT INTO reviews (isbn, username, comment, rating) VALUES (:isbn, :username, :comment, :rating)", {"isbn": isbn, "username": username, "comment": comment, "rating": rating})
        db.commit()

        flash('Review submitted successfully.', 'success')

        # Redirect back to the book page
        return redirect(url_for('book', isbn=isbn))


@app.route('/delete_review/<isbn>', methods=['POST'])
def delete_review(isbn):
    if 'username' not in session:
        flash('You must be logged in to delete a review.', 'error')
        return redirect(url_for('login'))

    # Get the current user's username from the session
    username = session['username']

    # Check if the user has already submitted a review for this book
    existing_review = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND username = :username", {"isbn": isbn, "username": username}).fetchone()
    if not existing_review:
        flash("You haven't submitted a review for this book.", 'error')
        return redirect(url_for('book', isbn=isbn))

    # Delete the review from the database
    db.execute("DELETE FROM reviews WHERE isbn = :isbn AND username = :username", {"isbn": isbn, "username": username})
    db.commit()

    flash("Your review has been successfully deleted.", 'success')

    # Redirect back to the book page
    return redirect(url_for('book', isbn=isbn))



if __name__ == '__main__':
    app.run(debug=True)
