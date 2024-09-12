from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, PasswordField, SelectField
from wtforms.validators import DataRequired


class BusinessForm(FlaskForm):
    BusinessName = StringField(label = 'Business Name')
    url = StringField(label = 'Profile URL', validators=[DataRequired()])
    category = SelectField(
        label='Category', 
        choices=[
            ('Roofing Contractor', 'Roofing Contractor'), 
            ('Concrete Contractor', 'Concrete Contractor'), 
            ('General Contractor', 'General Contractor'), 
            ('Insulation Contractor', 'Insulation Contractor'), 
            ('Countertop Contractor', 'Countertop Contractor'), 
            ('Drainage Services', 'Drainage Services'), 
            ('Gutter Service', 'Gutter Service'), 
            ('Credit Counseling Services', 'Credit Counseling Services'), 
            ('Property Investment', 'Property Investment')
        ]
    )
    ReviewsCount = IntegerField()
    Review = IntegerField()
    submit = SubmitField(label='Submit')

class LoginForm(FlaskForm):
    username = StringField(label = 'User Name: ', validators=[DataRequired()])
    password = PasswordField(label = 'Password:',validators=[DataRequired()])
    submit = SubmitField(label='Login')