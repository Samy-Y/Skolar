from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management
login_manager = LoginManager()
login_manager.init_app(app)  # Initialize the LoginManager with the Flask app

# Function to initialize the SQLite database
def init_db():
    conn = sqlite3.connect('users.db')  # Connect to the SQLite database
    cursor = conn.cursor()
    # Create the users table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    conn.commit()  # Commit the changes
    conn.close()  # Close the connection

init_db()  # Call the function to initialize the database

# User class inheriting from UserMixin for user authentication
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# User loader function to load a user from the database based on user ID
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('users.db')  # Connect to the SQLite database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()  # Fetch the user data
    conn.close()  # Close the connection
    if user:
        # Return a User object if the user is found
        return User(id=user[0], username=user[1], password=user[2])
    return None  # Return None if the user is not found

@app.route("/")
def index():
    return render_template("index.html")  # Render the index.html template

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Get the username and password from the form
        username = request.form["username"]
        print(username)
        password = request.form["password"]
        conn = sqlite3.connect('users.db')  # Connect to the SQLite database
        cursor = conn.cursor()
        # Check if the username and password match a user in the database
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()  # Fetch the user data
        conn.close()  # Close the connection
        if user:
            # Create a User object and log in the user
            user_obj = User(id=user[0], username=user[1], password=user[2])
            login_user(user_obj)
            session['user_id'] = user[0]
            session['username'] = username # Store the user ID in the session
            return redirect(url_for("dashboard"))  # Redirect to the dashboard
    return render_template("login.html")  # Render the login.html template

@app.route("/dashboard")
@login_required  # Ensure that only logged-in users can access this route
def dashboard():
    return render_template("dashboard.html", username=session.get('username', 'Guest'))  # Retrieve the username from the session

@app.route("/logout")
@login_required  # Ensure that only logged-in users can access this route
def logout():
    logout_user()  # Log out the user
    session.pop('user_id', None)  # Remove the user ID from the session
    return redirect(url_for("index"))  # Redirect to the index page

if __name__ == "__main__":
    app.run(debug=True)  # Run the Flask app in debug mode