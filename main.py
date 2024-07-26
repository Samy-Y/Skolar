from flask import Flask, render_template, request, redirect, url_for, session, flash
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
    author TEXT NOT NULL,
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

@app.route("/manage", methods=['GET','POST'])
@login_required
def manage():

    # DATA FETCHING AREA

    def get_teachers():
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE usertype = ?", (2,))
        
        teachers = cursor.fetchall()
        
        conn.close()
        
        return teachers
    
    def get_students():
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE usertype = ?", (3,))
        
        students = cursor.fetchall()
        
        conn.close()
        
        return students
    
    # STUDENT MANAGEMENT AREA

    def add_student():
        username = request.form.get("username")
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        birthdate = request.form.get("birthdate")
        classlvl = request.form.get("classlvl")

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, fname, usertype, password, birthdate, classlvl) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (username, email, name, 3, password, birthdate, classlvl))
            conn.commit()
        except sqlite3.Error as e:
            flash(f"An error occurred: {e}", "danger")
        finally:
            conn.close()

        return redirect(url_for('manage'))
    
    def edit_student():
        student_username = request.form.get("student_username")
        new_name = request.form.get("new_name")
        new_email = request.form.get("new_email")
        new_password = request.form.get("new_password")
        new_birthdate = request.form.get("new_birthdate")
        new_classlvl = request.form.get("new_classlvl")

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        if new_name:
            cursor.execute("UPDATE users SET fname = ? WHERE username = ?", (new_name, student_username))
        if new_email:
            cursor.execute("UPDATE users SET email = ? WHERE username = ?", (new_email, student_username))
        if new_password:
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, student_username))
        if new_birthdate:
            cursor.execute("UPDATE users SET birthdate = ? WHERE username = ?", (new_birthdate, student_username))
        if new_classlvl:
            cursor.execute("UPDATE users SET classlvl = ? WHERE username = ?", (new_classlvl, student_username))
        
        conn.commit()
        conn.close()

    def delete_student():
        student_username = request.form.get("student_username")
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM users WHERE username = ?", (student_username,))
        
        conn.commit()
        conn.close()

    if request.method == "POST":
        if 'add_student' in request.form:
            add_student()
        elif 'edit_student' in request.form:
            edit_student()
        elif 'delete_student' in request.form:
            delete_student()

    # TEACHER MANAGEMENT AREA

    def add_teacher():
        username = request.form.get("username")
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        birthdate = request.form.get("birthdate")
        classlvl = request.form.get("classlvl")

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (username, email, fname, usertype, password, birthdate, classlvl) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (username, email, name, 2, password, birthdate, classlvl))
            conn.commit()
            flash("Teacher added successfully!", "success")
        except sqlite3.Error as e:
            flash(f"An error occurred: {e}", "danger")
        finally:
            conn.close()

        return redirect(url_for('manage'))
    
    teachers = get_teachers()
    all_teachers_dict = {}
    for x in teachers:
        all_teachers_dict[f'ID{x[0]}'] = {
            'Username':x[1],
            'E-Mail':x[2],
            'Full Name':x[3],
            'Password':x[5],
            'Birth date':x[6],
            'Classes':x[7].split(',')
        }

    students = get_students()
    all_students_dict = {}
    for x in students:
        all_students_dict[f'ID{x[0]}'] = {
            'Username':x[1],
            'E-Mail':x[2],
            'Full Name':x[3],
            'Password':x[5],
            'Birth date':x[6],
            'Classes':x[7]
        }
    
    return render_template("managedb.html",
                           username=session.get('username', 'Guest'), 
                           usertype=session.get('usertype','Error'), 
                           f_name=session.get('fullname','Error'),
                           teachers_list=all_teachers_dict,
                           students_list=all_students_dict,
                           available_classes=available_classes)

##### UPLOAD PART #####
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
            cursor.execute("INSERT INTO resources (filename, author, class_level) VALUES (?, ?)", (filename, session.get["fullname"], class_level))
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
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)  # Remove the user ID from the session
    return redirect(url_for("index"))

@app.route('/resources')
def resources():
    return "<h2>Work In Progress</h2>"

if __name__ == "__main__":
    app.run(debug=True) 