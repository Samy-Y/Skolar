from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import os
import datetime
from werkzeug.utils import secure_filename
import json

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
def init_resourceDB():
    conn = sqlite3.connect('resources.db')
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        date TEXT NOT NULL,
        description TEXT NOT NULL,
        classes TEXT NOT NULL,
        visibility INTEGER NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

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
        return User(id=user[0], username=user[1], email=user[2], fname=user[3], 
                    usertype=user[4], password=user[5], birthdate=user[6], classlvl=user[7])
    return None  # Return None if the user is not found

# Blog directory
BLOG_DIR = './blog'

# Ensure the blog directory exists
os.makedirs(BLOG_DIR, exist_ok=True)

# User class and database initialization as before...

@app.route("/")
def index():
    # Fetch the latest 4 articles
    articles = get_latest_articles(limit=4)
    return render_template("index.html", articles=articles)

@app.route("/blog_articles")
def blog_articles():
    # Fetch all articles for the main blog page
    articles = get_all_articles()
    return render_template("blog_articles.html", articles=articles)

@app.route("/article/<string:title>")
def view_article(title):
    # Render a specific article
    article = load_article(title)
    if article:
        return render_template("article.html", article=article)
    else:
        flash("Article not found.", "danger")
        return redirect(url_for("blog_articles"))

@app.route("/create_article", methods=["GET", "POST"])
@login_required
def create_article():
    if session.get('usertype') >= 2:
        flash("You do not have permission to create articles.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        thumbnail = request.files.get("thumbnail")

        if not title or not content:
            flash("Title and content are required.", "danger")
        else:
            thumbnail_url = None
            if thumbnail:
                filename = secure_filename(thumbnail.filename)
                thumbnail.save(os.path.join(BLOG_DIR, filename))
                thumbnail_url = url_for('static', filename=f'blog/{filename}')

            # Save article as JSON
            article = {
                "title": title,
                "content": content,
                "thumbnail_url": thumbnail_url
            }
            save_article(article)
            flash("Article created successfully!", "success")
            return redirect(url_for("dashboard"))

    return render_template("create_article.html")

def get_latest_articles(limit=4):
    articles = []
    for filename in os.listdir(BLOG_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(BLOG_DIR, filename), 'r') as file:
                article = json.load(file)
                articles.append(article)
    # Sort articles by title for now
    articles.sort(key=lambda x: x["title"])
    return articles[:limit]

def get_all_articles():
    articles = []
    for filename in os.listdir(BLOG_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(BLOG_DIR, filename), 'r') as file:
                article = json.load(file)
                articles.append(article)
    # Sort articles by title
    articles.sort(key=lambda x: x["title"])
    return articles

def load_article(title):
    filename = f"{title}.json"
    filepath = os.path.join(BLOG_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            return json.load(file)
    return None

def save_article(article):
    title = article['title']
    filename = f"{title}.json"
    filepath = os.path.join(BLOG_DIR, filename)
    with open(filepath, 'w') as file:
        json.dump(article, file)

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
            print(f"New login: {{username}}")
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
            if user[4] < 2:
                session['user_classes'] = [x for x in range(1,13)]
            else:
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
    if session['usertype'] == 0:
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
        
        teachers = get_teachers()
        all_teachers_dict = {}
        for x in teachers:
            all_teachers_dict[f'ID{x[0]}'] = {
                'Username':x[1],
                'E-Mail':x[2],
                'Full Name':x[3],
                'Password':x[5],
                'Birth date':x[6],
                'Classes':x[7]
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
        
        def edit_teacher():
            teacher_username = request.form.get("teacher_username")
            new_name = request.form.get("new_name")
            new_email = request.form.get("new_email")
            new_password = request.form.get("new_password")
            new_birthdate = request.form.get("new_birthdate")
            new_classlvl = request.form.get("new_classlvl")

            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            if new_name:
                cursor.execute("UPDATE users SET fname = ? WHERE username = ?", (new_name, teacher_username))
            if new_email:
                cursor.execute("UPDATE users SET email = ? WHERE username = ?", (new_email, teacher_username))
            if new_password:
                cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, teacher_username))
            if new_birthdate:
                cursor.execute("UPDATE users SET birthdate = ? WHERE username = ?", (new_birthdate, teacher_username))
            if new_classlvl:
                cursor.execute("UPDATE users SET classlvl = ? WHERE username = ?", (new_classlvl, teacher_username))
            
            conn.commit()
            conn.close()

        def delete_teacher():
            teacher_username = request.form.get("teacher_username")
            
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM users WHERE username = ?", (teacher_username,))
            
            conn.commit()
            conn.close()

        if request.method == "POST":
            if 'add_student' in request.form:
                add_student()
            elif 'edit_student' in request.form:
                edit_student()
            elif 'delete_student' in request.form:
                delete_student()

            elif 'add_teacher' in request.form:
                add_teacher()
            elif 'edit_teacher' in request.form:
                edit_teacher()
            elif 'delete_teacher' in request.form:
                delete_teacher()
            return render_template("managedb.html",
                            username=session.get('username', 'Guest'), 
                            usertype=session.get('usertype','Error'), 
                            f_name=session.get('fullname','Error'),
                            teachers_list=all_teachers_dict,
                            students_list=all_students_dict,
                            available_classes=available_classes)
        
        return render_template("managedb.html",
                            username=session.get('username', 'Guest'), 
                            usertype=session.get('usertype','Error'), 
                            f_name=session.get('fullname','Error'),
                            teachers_list=all_teachers_dict,
                            students_list=all_students_dict,
                            available_classes=available_classes)
    
    else:
        return redirect(url_for('dashboard'))

##### UPLOAD PART #####

DATABASE = 'resources.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_resource():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['file']
        
        # Correctly handle the visibility checkbox
        visibility = request.form.get('visibility') == '1'
        
        classes = []
        for x in request.form.getlist('classes'):
            classes.append(available_classes.index(x))
        print(classes)
        classes = ",".join(map(str, classes))
        
        author = session.get('fullname', 'Unknown')

        filepath = f'uploads/{file.filename}'
        file.save(filepath)

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO resources (url, title, author, date, description, classes, visibility) VALUES (?, ?, ?, datetime('now'), ?, ?, ?)",
            (filepath, title, author, description, classes, visibility)
        )
        conn.commit()
        conn.close()

        flash('Resource uploaded successfully')  # Note to future self: Does flash still exist?
        return redirect(url_for('resource_manage'))
    
    return redirect(url_for('resource_manage'))

@app.route('/delete', methods=['POST'])
@login_required
def delete_resource():
    resource_id = request.form['resource_id']
    
    conn = get_db_connection()
    resource = conn.execute('SELECT url FROM resources WHERE id = ?', (resource_id,)).fetchone()
    print(resource)
    if resource:
        file_path = resource['url'] # Remove file
        if os.path.exists(file_path):
            os.remove(file_path)

        conn.execute('DELETE FROM resources WHERE id = ?', (resource_id,))
        conn.commit()

        flash('Resource deleted successfully')
    else:
        flash('Resource not found or already deleted')

    conn.close()

    return redirect(url_for('resource_manage'))
    
@app.route('/change_visibility',methods=['POST'])
def change_visibility():
    resource_id = request.form['resource_id']
    
    conn = get_db_connection()
    result = conn.execute('SELECT visibility FROM resources WHERE id = ?', (resource_id,)).fetchone()
    if result is not None:
        current_visibility = result['visibility']  # Or result[0] if using index
    else:
        print("Resource not found.")

    new_visibility = 0 if current_visibility == 1 else 1

    conn.execute('UPDATE resources SET visibility = ? WHERE id = ?', (new_visibility, resource_id))
    conn.commit()

    conn.commit()

    conn.close()

    return redirect(url_for('resource_manage'))

@app.route("/resource_manage", methods=["GET", "POST"])
@login_required
def resource_manage():
    user_classes = None
    if session['usertype'] < 3:
        conn = sqlite3.connect('resources.db')
        cursor = conn.cursor()
        resources = None
        if session['usertype'] == 2:
            cursor.execute("SELECT * FROM resources WHERE author = ?", (session['fullname'],))
            resources = cursor.fetchall()
            user_classes = [available_classes[int(x)-1] for x in session.get('user_classes').split(',')]
        else:
            cursor.execute("SELECT * FROM resources")
            resources = cursor.fetchall()
            user_classes = available_classes
        conn.close()
        resource_list = []
        # Convert resources to a list of dictionaries for easier template rendering
        try:
            resource_list = [{
                'id':r[0],
                'url': r[1],
                'title': r[2],
                'author': r[3],
                'date': r[4],
                'description': r[5],
                'classes': ";".join([available_classes[int(x)] for x in r[6].split(',')]),
                'visibility': r[7]
            } for r in resources]
        except ValueError:
            resource_list = []
            print("There was an error loading a few resources by",session['username'])
        return render_template("resource_manage.html", resources=resource_list,
                            user_classes=user_classes,
                            usertype=session.get('usertype'))
    else:
        return redirect(url_for('dashboard'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)  # Remove the user ID from the session
    return redirect(url_for("index"))

@app.route('/resource_view')
@login_required
def resource_view():
    if session['usertype'] != 3:
        # Redirect non-student users
        return redirect(url_for('resource_manage'))

    # Fetch the user's class level from the session
    user_classes = session.get('user_classes')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch resources that match the student's classes and are visible
    cursor.execute("""
        SELECT * FROM resources
        WHERE visibility = 1
    """)
    
    resources = cursor.fetchall()
    conn.close()

    # Filter resources that are relevant to the user's classes
    resource_list = [
        {
            'id': r[0],
            'url': r[1],
            'title': r[2],
            'author': r[3],
            'date': r[4],
            'description': r[5],
            'classes': ";".join([available_classes[int(x)] for x in r[6].split(',')]),
            'visibility': r[7]
        }
        for r in resources
        if user_classes in r[6].split(',')
    ]

    return render_template("resource_view.html", resources=resource_list, fullname = session.get('fullname'))


if __name__ == "__main__":
    init_resourceDB()
    app.run(host="0.0.0.0",debug=True) 