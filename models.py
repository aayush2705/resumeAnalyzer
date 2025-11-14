from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# =====================================================
# USER MODEL
# =====================================================
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # candidate or admin

    # Relationships
    resumes = db.relationship("Resume", backref="user", lazy=True)
    feedbacks = db.relationship("Feedback", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"


# =====================================================
# RESUME MODEL
# =====================================================
class Resume(db.Model):
    __tablename__ = "resume"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # ------------ File Storage (PostgreSQL BYTEA) ------------
    file_name = db.Column(db.String(200), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=False)     # <-- store bytes
    file_mime = db.Column(db.String(50), nullable=False)      # <-- pdf/doc/docx

    # ------------ Parsed & AI-generated fields ------------
    parsed_text = db.Column(db.Text)
    skills = db.Column(db.Text)
    experience = db.Column(db.String(100))
    suggested_roles = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    predicted_role = db.Column(db.String(100))
    recommended_skills = db.Column(db.Text)
    resume_score = db.Column(db.Float)
    tips = db.Column(db.Text)

    # ------------ Additional fields ------------
    courses = db.Column(db.Text)
    course_links = db.Column(db.Text)
    candidate_name = db.Column(db.String(255))
    candidate_level = db.Column(db.String(50))  

    def __repr__(self):
        return f"<Resume {self.file_name} for User {self.user_id}>"



# =====================================================
# FEEDBACK MODEL
# =====================================================
class Feedback(db.Model):
    __tablename__ = "feedback"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    rating = db.Column(db.String(50), nullable=False)  # rating as text
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Feedback {self.name} ({self.email})>"


# =====================================================
# COURSE MODEL
# =====================================================
class Course(db.Model):
    __tablename__ = "courses"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)   # e.g., Data Science, Web Dev
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"<Course {self.name} ({self.category})>"
