from wtforms import Form, StringField, RadioField, SelectField, TextAreaField, validators, IntegerField
from wtforms.fields import EmailField, DateField

class CreateUserForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    gender = SelectField('Gender', [validators.DataRequired()], choices=[('', 'Select'), ('F', 'Female'), ('M', 'Male')], default='')
    membership = RadioField('Membership', choices=[('F', 'Fellow'), ('S', 'Senior'), ('P', 'Professional')], default='F')
    remarks = TextAreaField('Remarks', [validators.Optional()])

class CreateCustomerForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    gender = SelectField('Gender', [validators.DataRequired()], choices=[('', 'Select'), ('F', 'Female'), ('M', 'Male')], default='')
    email = EmailField('Email', [validators.Email(), validators.DataRequired()])
    date_joined = DateField('Date Joined', format='%Y-%m-%d')
    address = TextAreaField('Mailing Address', [validators.length(max=200), validators.DataRequired()])
    membership = RadioField('Membership', choices=[('F', 'Fellow'), ('S', 'Senior'), ('P', 'Professional')], default='F')
    remarks = TextAreaField('Remarks', [validators.Optional()])
class CreateEbookForm(Form):
    title = StringField('Title', [validators.DataRequired(), validators.Length(min=1, max=200)])
    description = TextAreaField('Description', [validators.Optional(), validators.Length(max=500)])
    author = StringField('Author', [validators.DataRequired(), validators.Length(min=1, max=100)])
    genre = StringField('Genre', [validators.DataRequired(), validators.Length(min=1, max=100)])
    price = IntegerField('Price', [validators.DataRequired(), validators.NumberRange(min=1, max=100)])