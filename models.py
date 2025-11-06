from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ------------------- USER MODEL ------------------- #
class User(db.Model):
    __tablename__ = 'user'  # explicit table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # candidate or admin

    # Relationships
    resumes = db.relationship('Resume', backref='user', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"

# ------------------- RESUME MODEL ------------------- #
class Resume(db.Model):
    __tablename__ = 'resume'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    parsed_text = db.Column(db.Text)
    skills = db.Column(db.Text)
    experience = db.Column(db.String(100))
    suggested_roles = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    predicted_role = db.Column(db.String(100))
    recommended_skills = db.Column(db.Text)
    resume_score = db.Column(db.Float)
    tips = db.Column(db.Text)

    # ✅ Added new fields
    courses = db.Column(db.Text)
    course_links = db.Column(db.Text)

    def __repr__(self):
        return f"<Resume {self.file_name} for User ID {self.user_id}>"

# ------------------- FEEDBACK MODEL ------------------- #
class Feedback(db.Model):
    __tablename__ = 'feedback'
    __table_args__ = {'extend_existing': True}  # ✅ avoids redefinition error
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    rating = db.Column(db.String(50), nullable=False)  # ✅ changed from Integer to String
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------- COURSE MODEL ------------------- #
class Course(db.Model):
    __tablename__ = 'courses'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)  # e.g. Data Science, Web Development, etc.
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"<Course {self.name} ({self.category})>"


    def __repr__(self):
        return f"<Feedback from {self.name} ({self.email}) - Rating {self.rating}>"