from wtforms import Form, StringField, RadioField, SelectField, TextAreaField, validators, IntegerField
from wtforms.fields import EmailField, DateField

class CreateCardForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    card_number = StringField('Card_Number', [validators.DataRequired(), validators.Length(min=16, max=16)])
    expiry_date = DateField('Expiry Date', [validators.DataRequired()], format='%Y-%d-%m')
    cvc_number = StringField('CVC', [validators.DataRequired(), validators.Length(min=3, max=3)])

class CreateCustomerForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    gender = SelectField('Gender', [validators.DataRequired()],
                         choices=[('', 'Select'), ('F', 'Female'), ('M', 'Male')],
                         default='')
    email = EmailField('Email', [validators.Email(), validators.DataRequired()])
    date_joined = DateField('Date Joined', format='%Y-%m-%d')
    address = TextAreaField('Mailing Address', [validators.length(max=200), validators.DataRequired()])
    membership = RadioField('Membership', choices=[('F', 'Fellow'), ('S', 'Senior'), ('P', 'Professional')],
                            default='F')
    remarks = TextAreaField('Remarks', [validators.Optional()])