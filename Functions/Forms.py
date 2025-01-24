from flask_wtf.file import FileRequired, FileAllowed
from wtforms import Form, StringField, validators, FileField
from wtforms.fields import DateField
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import FloatField, IntegerField
from wtforms.fields.simple import TextAreaField, PasswordField


class CreateCardForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    card_number = StringField('Card_Number', [validators.DataRequired(), validators.Length(min=16, max=16)])
    expiry_date = DateField('Expiry Date', [validators.DataRequired()], format='%Y-%m-%d')
    cvc_number = StringField('CVC', [validators.DataRequired(), validators.Length(min=3, max=3)])



class CreateEbookForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200), validators.DataRequired()])
    author = StringField('Author', [validators.Length(min=1, max=150), validators.DataRequired()])
    description = TextAreaField('Description', [validators.Optional()])
    price = FloatField('Price', [validators.DataRequired(), validators.NumberRange(min=0)])
    genre = StringField('Genre', [validators.Length(min=1, max=100), validators.DataRequired()])
    image = FileField('Ebook Cover Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    content = FileField('Ebook Content (PDF)', validators=[FileAllowed(['pdf'], 'PDF files only!')])


class CreateReviewForm(Form):
    stars = IntegerField('Stars', [validators.NumberRange(min=1, max=5), validators.DataRequired()])
    message = TextAreaField('Message', [validators.Length(min=1, max=500), validators.DataRequired()])
    reviewer_name = StringField('Your Name', [validators.Length(min=1, max=150), validators.DataRequired()])

class CreateUserForm(Form):
    username = StringField('Username', [validators.Length(min=1, max=150), validators.DataRequired()])
    email = StringField('Email', [validators.Email(), validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
    role = SelectField('Role', [validators.DataRequired()], choices=[('User', 'User'), ('Staff', 'Staff')],
                       default='User')