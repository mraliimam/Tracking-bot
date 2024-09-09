from market import db
from market import bcrypt, login_manager
from flask_login import UserMixin
from market import app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    role = db.Column(db.String(), nullable=False, default='user')

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

class ScrapeData(db.Model):
    from datetime import datetime
    import pytz
    new_york_date = datetime.now(pytz.timezone('America/New_York')).date()

    id = db.Column(db.Integer(), primary_key=True)
    business_name = db.Column(db.String(), nullable=True)
    nick_name = db.Column(db.String(), nullable=True)
    url = db.Column(db.String(), nullable=False)
    date = db.Column(db.Date(), nullable=False, default=new_york_date)
    reviews_count = db.Column(db.Integer(), default=0)
    # review = db.Column(db.Integer(), nullable=False)
    
# db.create_all()