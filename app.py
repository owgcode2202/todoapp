from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.secret_key = 'some_random_key'
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Task {self.id}>'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    todos = db.relationship('Todo', backref='author', lazy=True)

with app.app_context():
    db.create_all()
            
@app.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content, user_id=current_user.id)
        
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for('dashboard'))
        except:
            return 'there is an issue adding the task'
    
    else: 
        tasks = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.date_created).all()
        return render_template('index.html', tasks=tasks)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task = Todo.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('You are not authorized to delete this task')
        return redirect(url_for('dashboard'))
    
    try:
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('dashboard'))
    except:
        return 'issue deleting task'

@app.route('/update/<int:id>', methods = ['GET', 'POST'])
@login_required
def update(id):
    task = Todo.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('You are not authorized to update this task')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect(url_for('dashboard'))
        except:
            return 'issue updating task'
            
    else:
        return render_template('update.html', task=task)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # Check if username already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists!')
            return render_template('register.html')
        
        # Check if email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists!')
            return render_template('register.html')

        new_user = User(username=username, email=email, password=hashed_password)
            
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('landing'))
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")  
            flash('Registration failed. Please try again.')
            return render_template('register.html')
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
            return render_template('login.html')

    return render_template('login.html')
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)