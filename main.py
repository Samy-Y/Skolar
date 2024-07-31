from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import os
import datetime
from werkzeug.utils import secure_filename
import json
import re

start = datetime.datetime.now()

app = Flask(__name__)
app.secret_key = 'something unique and secret'
login_manager = LoginManager()
login_manager.init_app(app) 

# General information about the database:
# User types:
# Level 0: Administrator, full control
# Level 1: Blog manager
# Level 2: Teacher
# Level 3: Student

available_classes = ["CP","CE1","CE2","CM1","CM2","6e","1AC","2AC","3AC","TC","1Bac","2Bac"]
# Index in DB starts at 1. Crappy ahh Database management system

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
BLOG_DIR = './static/blog'

# Ensure the blog directory exists
os.makedirs(BLOG_DIR, exist_ok=True)

# User class and database initialization as before...

@app.route("/")
def index():
    # Fetch the latest 4 articles
    articles = get_latest_articles(limit=4)
    return render_template("index.html", articles=articles)

def get_latest_articles(limit=4):
    articles = []
    for filename in os.listdir(BLOG_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(BLOG_DIR, filename), 'r') as file:
                article = json.load(file)
                article['title'] = sanitize_filename(article['title'])
                articles.append(article)
    # Sort articles by title for now
    return articles[:limit]

def get_all_articles():
    articles = []
    for filename in os.listdir(BLOG_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(BLOG_DIR, filename), 'r') as file:
                article = json.load(file)
                article['title'] = sanitize_filename(article['title'])
                article['content'] = sanitize_filename(article['content'])
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

def sanitize_filename(title):
    # Define replacements for forbidden characters with their HTML entity counterparts
    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        ':': '&colon;',
        '"': '&quot;',
        '/': '&sol;',
        '\\': '&bsol;',
        '|': '&vert;',
        '?': '&quest;',
        '*': '&ast;',
    }
    
    # Replace forbidden characters with their HTML entity counterparts
    safe_title = re.sub(
        r'[<>:"/\\|?*]', 
        lambda match: replacements[match.group(0)], 
        title
    )
    
    return safe_title.strip()

def save_article(article):
    title = article['title']
    safe_title = sanitize_filename(title)  # Sanitize the title for a safe filename
    filename = f"{safe_title}.json"
    filepath = os.path.join(BLOG_DIR, filename)
    try:
        with open(filepath, 'w') as file:
            json.dump(article, file, indent=4)  # Use indent for pretty printing
        print(f"Article '{title}' saved successfully.")
    except Exception as e:
        print(f"Error saving article '{title}': {e}")

@app.route("/blog_articles")
def blog_articles():
    # Fetch all articles for the main blog page
    articles = get_all_articles()
    return render_template("blog/blog_articles.html", articles=articles)

@app.route("/article/<string:title>")
def view_article(title):
    # Convert the sanitized title back to the original
    article = load_article(title)
    if article:
        return render_template(
            "blog/article.html", 
            article_title=article['title'],
            article_content=article['content'].replace("\n", "<br>"),
            article_date=article['date'],
            article_thumbnail_url=article['thumbnail_url']
        )
    else:
        flash("Article not found.", "danger")
        return redirect(url_for("blog_articles"))

@app.route("/create_article", methods=["GET", "POST"])
@login_required
def create_article():
    if session.get('usertype') >= 2:
        abort(404)

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
                file_path = os.path.join(BLOG_DIR+"/"+filename)

                if os.path.isfile(file_path):
                    name, ext = os.path.splitext(filename)
                    i = 1
                    while os.path.isfile(file_path):
                        new_filename = f"{name}({i}){ext}"
                        file_path = os.path.join(BLOG_DIR, new_filename)
                        i += 1
                    filename = new_filename

                thumbnail.save(file_path)
                thumbnail_url = url_for('static', filename=f'blog/{filename}')

            # Save article as JSON
            article = {
                "title": title,
                "date": datetime.date.today().strftime("%d/%m/%Y"),
                "author": session.get('fullname'),
                "content": content,
                "thumbnail_url": thumbnail_url
            }
            save_article(article)
            return redirect(url_for("manage_blog",success=True,title=title))

    return render_template("blog/create_article.html")

@app.route("/manage_blog", methods=["GET"])
@login_required
def manage_blog():
    articles = get_all_articles()
    return render_template("blog/manage_blog.html", articles=articles)

@app.route("/edit_article/<string:title>", methods=["GET", "POST"])
@login_required
def edit_article(title):
    if request.method == "POST":
        new_title = request.form.get("title")
        new_content = request.form.get("content")
        new_thumbnail = request.files.get("thumbnail")

        article = load_article(title)
        if article:
            if new_thumbnail:
                new_filename = secure_filename(new_thumbnail.filename)
                new_thumbnail.save(os.path.join(BLOG_DIR, new_filename))
                thumbnail_url = url_for('static', filename=f'blog/{new_filename}')
                article['thumbnail_url'] = thumbnail_url

            article['title'] = new_title
            article['content'] = new_content
            save_article(article)
            flash("Article updated successfully!", "success")
            return redirect(url_for("manage_blog"))
        else:
            flash("Article not found.", "danger")
            return redirect(url_for("manage_blog"))
    
    article = load_article(title)
    if article:
        return render_template("blog/edit_article.html", article=article)
    else:
        flash("Article not found.", "danger")
        return redirect(url_for("manage_blog"))

@app.route("/delete_article/<string:title>", methods=["POST"])
@login_required
def delete_article(title):
    filename = f"{title}.json"
    filepath = os.path.join(BLOG_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash("Article deleted successfully!", "success")
    else:
        flash("Article not found.", "danger")
    return redirect(url_for("manage_blog"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get('authenticated'):
        return redirect(url_for('dashboard'))
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
            print(f"{username} has logged in!")
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
            session['authenticated'] = True
            if user[4] < 2:
                session['user_classes'] = [x for x in range(1,13)]
            else:
                session['user_classes'] = user[7]
            return redirect(url_for("dashboard"))  # Redirect to the dashboard
        else:
            return redirect(url_for('login',failed=True))
    return render_template("login.html")  # Render the login.html template

@app.route("/dashboard")
@login_required  # Ensure that only logged-in users can access this route
def dashboard():
    print(f"{session.get('username')} has accessed the dashboard.")
    if session.get('usertype') == 3:
        user_classes=session.get('user_classes')
        name_user_class = available_classes[int(user_classes)]
        return render_template("dashboard.html",
                           username=session.get('username', 'Guest'),
                           usertype=session.get('usertype','Error'),
                           name_user_class=name_user_class,
                           f_name=session.get('fullname','Error'))  # Retrieve the username from the session
    else:
        return render_template("dashboard.html",
                           username=session.get('username', 'Guest'),
                           usertype=session.get('usertype','Error'), 
                           f_name=session.get('fullname','Error'))  # Retrieve the username from the session

@app.route("/manage_users", methods=['GET','POST'])
@login_required
def manage_users():
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
                print(f"An error has occured while {session.get('username')} tried to add a student! \n"+e)
            finally:
                conn.close()

            return redirect(url_for('manage_users'))
        
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
                print(f"An error has occured while {session.get('username')} tried to add a teacher! \n"+e)
            finally:
                conn.close()

            return redirect(url_for('manage_users'))
        
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
            return render_template("manage_users.html",
                            username=session.get('username', 'Guest'), 
                            usertype=session.get('usertype','Error'), 
                            f_name=session.get('fullname','Error'),
                            teachers_list=all_teachers_dict,
                            students_list=all_students_dict,
                            available_classes=available_classes)
        
        return render_template("manage_users.html",
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

def get_rs_db_connection():
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
        if request.form.getlist('classes'):
            for x in request.form.getlist('classes'):
                classes.append(available_classes.index(x))
            print(classes)
            classes = ",".join(map(str, classes))
        else:
            return redirect(url_for('resource_manage',failed='True'))
        
        author = session.get('fullname', 'Unknown')

        filepath = f'uploads/{file.filename}'
        file.save(filepath)

        conn = get_rs_db_connection()
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
    
    conn = get_rs_db_connection()
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
    
    conn = get_rs_db_connection()
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
            user_classes = [available_classes[int(x)] for x in session.get('user_classes').split(',')]
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
            print(resource_list)
            print("There was an error loading a few resources by",session['username'])
        return render_template("resource_manage.html", resources=resource_list,
                            user_classes=user_classes,
                            usertype=session.get('usertype'))
    else:
        return redirect(url_for('dashboard'))


@app.route("/system_info")
@login_required
def system_info():
    if session.get('usertype') != 0:
        abort(404)
    
    system_status = {
        "uptime": (datetime.datetime.now() - start).seconds
    }
    user_db_cursor = sqlite3.connect("users.db").cursor()

    total_users = len(user_db_cursor.execute("""SELECT id FROM users""").fetchall())
    total_students = len(user_db_cursor.execute("""SELECT id FROM users WHERE usertype = 3""").fetchall())
    total_teachers = len(user_db_cursor.execute("""SELECT id FROM users WHERE usertype = 2""").fetchall())
    total_managers = len(user_db_cursor.execute("""SELECT id FROM users WHERE usertype = 1""").fetchall())
    total_admins = len(user_db_cursor.execute("""SELECT id FROM users WHERE usertype = 0""").fetchall())

    user_stats = {
        "total_users": total_users,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_managers": total_managers,
        "total_admins": total_admins
    }
    
    system_info = {
        "version": "0.9.0",
    }
    
    return render_template("system_info.html", system_status=system_status, user_stats=user_stats, system_info=system_info)


@app.route("/logout")
@login_required
def logout():
    print(f"{session.get('username')} has logged out!")
    logout_user()
    session.pop('user_id', None)  # Remove the user ID from the session
    session.pop('username', None)
    session.pop('usertype', None)
    session.pop('fullname', None)
    session.pop('user_classes', None)
    session.pop('authenticated', False)
    return redirect(url_for("index"))

@app.route('/resource_view')
@login_required
def resource_view():
    if session.get('usertype') != 3:
        # Redirect non-student users
        return redirect(url_for('resource_manage'))

    # Fetch the user's class level from the session
    user_classes = session.get('user_classes')

    conn = get_rs_db_connection()
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

def init_scheduleDB():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create schedule table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        class TEXT NOT NULL,
        time TEXT NOT NULL,
        FOREIGN KEY (teacher_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_all_schedules():
    schedules = []
    try:
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, u.fname AS teacher, s.class, s.time
                FROM schedules s
                JOIN users u ON s.teacher_id = u.id
            """)
            schedules = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        
    return schedules


def add_schedule(teacher_id, class_name, time):
    conn = sqlite3.connect('schedules.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO schedules (teacher_id, class, time) VALUES (?, ?, ?)", (teacher_id, class_name, time))
    conn.commit()
    conn.close()

def delete_schedule(schedule_id):
    conn = sqlite3.connect('schedules.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()

@app.route("/schedule_manage", methods=["GET", "POST"])
@login_required
def schedule_manage():
    if session['usertype'] != 0:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        teacher_id = request.form['teacher_id'] # aaaaactually it's teacher_fname 🤓
        class_name = request.form['class']
        time = request.form['time']
        add_schedule(teacher_id, class_name, time)
        return redirect(url_for('schedule_manage'))

    schedules = get_all_schedules()
    # Fetch all teachers for selection
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, fname FROM users WHERE usertype = 2")
    teachers = cursor.fetchall()
    print(teachers)
    conn.close()

    classes = available_classes  # Assuming available_classes contains the class names
    
    return render_template("schedule_manage.html", schedules=schedules, teachers=teachers, classes=classes)

@app.route("/delete_schedule", methods=["POST"])
@login_required
def delete_schedule_route():
    schedule_id = request.form['schedule_id']
    delete_schedule(schedule_id)
    return redirect(url_for('schedule_manage'))

@app.route("/schedule_view")
@login_required
def schedule_view():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    if session['usertype'] == 2:  # Teacher view
        cursor.execute("""
            SELECT s.class, s.time, u.fname AS teacher
            FROM schedules s
            JOIN users u ON s.teacher_id = u.id
            WHERE u.id = ?
        """, (session['user_id'],))
        schedules = cursor.fetchall()
    elif session['usertype'] == 3:  # Student view
        # Here you'd want to fetch relevant teachers for the student's classes
        cursor.execute("""
            SELECT s.class, s.time, u.fname AS teacher
            FROM schedules s
            JOIN users u ON s.teacher_id = u.id
            WHERE s.class IN (SELECT classlvl FROM users WHERE id = ?)
        """, (session['user_id'],))
        schedules = cursor.fetchall()
    else:
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template("schedule_view.html", schedules=schedules, fullname=session.get('fullname'))

## GRADES AREA ##

@app.route("/grades_view")
@login_required
def grades_view():
    # Fetch grades for the logged-in student
    student_username = session['username']
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT grade, author, date FROM grades WHERE student_username = ?", (student_username,))
    grades = cursor.fetchall()
    conn.close()
    return render_template("grades_view.html", grades=grades)

@app.route("/grades_manage", methods=["GET", "POST"])
@login_required
def grades_manage():
    usertype = session.get('usertype')
    if usertype == 2:  # Teacher
        # Only fetch grades for students in the teacher's class
        classlvl = session.get('user_classes')
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT student_username, grade, author, date FROM grades WHERE classlvl = ?", (classlvl,))
        grades = cursor.fetchall()
        conn.close()
        return render_template("grades_manage.html", grades=grades, usertype=usertype)
    
    elif usertype == 0:  # Admin
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM grades")  # Fetch all grades for Admin
        grades = cursor.fetchall()
        conn.close()

        grades_list = [{
            'student_username':g[0],
            'grade':g[1],
            'author':g[2],
            'date': g[3],
        } for g in grades]

        print(grades_list)
        return render_template("grades_manage.html", grades=grades, usertype=usertype)
    
    else:
        abort(404)

    abort(403)

@app.route("/submit_grade", methods=["POST"])
@login_required
def submit_grade():
    # Allow teachers to submit grades
    teacher_id = session['user_id']
    student_username = request.form['student_username']
    grade = request.form['grade']
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO grades (student_username, grade, author, date) VALUES (?, ?, ?, ?)",
                   (student_username, grade, session['fullname'], date))
    conn.commit()
    conn.close()
    return redirect(url_for("grades_manage"))

@app.route("/delete_grade", methods=["POST"])
@login_required
def delete_grade():
    # Admin functionality to delete a grade
    grade_id = request.form['grade_id']
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grades WHERE id = ?", (grade_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("grades_manage"))

def init_gradesDB():
    conn = sqlite3.connect('users.db')
    
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_username TEXT NOT NULL,
            grade INTEGER NOT NULL,
            author TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_gradesDB()
    init_scheduleDB()
    init_resourceDB()
    app.run(host="0.0.0.0",debug=True) 