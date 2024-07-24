from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'something unique and secret'  # Secret key for session management
login_manager = LoginManager()
login_manager.init_app(app)  # Initialize the LoginManager with the Flask app

# General information about the database:
# User types:
# Level 0: Administrator, full control
# Level 1: Blog manager
# Level 2: Teacher
# Level 3: Student

available_classes = ["CP","CE1","CE2","CM1","CM2","6e","1AC","2AC","3AC","TC","1Bac","2Bac"]

# Database creation (resource management)
def initRDB():
    conn = sqlite3.connect("resources.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    class_level INTEGER NOT NULL)""")
    conn.commit()
    cursor.close()

initRDB()

# User class inheriting from UserMixin for user authentication
class User(UserMixin):
    def __init__(self, id, username, email, fname, usertype, password, birthdate, classlvl):
        self.id = id
        self.username = username
        self.email = email
        self.fname = fname
        self.usertype = usertype
        self.password = password
        self.birthdate = birthdate
        self.classlvl = classlvl

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
        return User(id=user[0], username=user[1], email=user[2], fname=user[3], usertype=user[4], password=user[5], birthdate=user[6], classlvl=user[7])
    return None  # Return None if the user is not found

@app.route("/")
def index():
    return render_template("index.html")  # Render the index.html template

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Get the username and password from the form
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect('users.db')  # Connect to the SQLite database
        cursor = conn.cursor()
        # Check if the username and password match a user in the database
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()  # Fetch the user data
        conn.close()  # Close the connection
        if user:
            print("User logged in!")
            # Create a User object and log in the user
            user_obj = User(id=user[0], 
                            username=user[1], 
                            email=user[2], 
                            fname=user[3], 
                            usertype=user[4], 
                            password=user[5], 
                            birthdate=user[6], 
                            classlvl=user[7])
            login_user(user_obj)
            session['user_id'] = user[0] # Store the user ID in the session (i forgot why i should do that lmao)
            session['username'] = username 
            session['fullname'] = user[3]
            session['usertype'] = user[4]
            session['user_classes'] = user[7]
            return redirect(url_for("dashboard"))  # Redirect to the dashboard
    return render_template("login.html")  # Render the login.html template

@app.route("/dashboard")
@login_required  # Ensure that only logged-in users can access this route
def dashboard():
    return render_template("dashboard.html",
                           username=session.get('username', 'Guest'),
                           usertype=session.get('usertype','Error'), 
                           f_name=session.get('fullname','Error'))  # Retrieve the username from the session

@app.route("/manage")
@login_required
def manage():
    return render_template("managedb.html",
                           username=session.get('username', 'Guest'), 
                           usertype=session.get('usertype','Error'), 
                           f_name=session.get('fullname','Error'))  # Retrieve the username from the session

# Set the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if session.get('usertype') > 2:
        return redirect(url_for('dashboard'))
    
    if request.method == "POST":
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        class_level = request.form.get('classlvl')
        
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            conn = sqlite3.connect('resources.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO resources (filename, class_level) VALUES (?, ?)", (filename, class_level))
            conn.commit()
            conn.close()
            return redirect(url_for('upload',success=True))
        

    if session.get('usertype') == 2:
        classes_teached = (session.get('user_classes')).split(',')
        classes_teached = map(int,classes_teached)
    elif session.get('usertype') <2:
        classes_teached = available_classes
    success = request.args.get('success')  # Retrieve the 'success' query parameter
    return render_template("resource_upload.html",
                           username=session.get('username', 'Guest'),
                           usertype=session.get('usertype', 'Error'),
                           f_name=session.get('fullname', 'Error'),
                           available_classes=available_classes, 
                           classes_teached=classes_teached,success=success)


@app.route("/logout")
@login_required  # Ensure that only logged-in users can access this route
def logout():
    logout_user()  # Log out the user
    session.pop('user_id', None)  # Remove the user ID from the session
    return redirect(url_for("index"))  # Redirect to the index page

if __name__ == "__main__":
    app.run(debug=True)  # Run the Flask app in debug mode