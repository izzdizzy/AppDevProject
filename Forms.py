from wtforms import Form, StringField, RadioField, SelectField, TextAreaField, validators
from wtforms.fields import EmailField, DateField
from wtforms.validators import DataRequired

class CreateUserForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=50), validators.DataRequired()])
    name = StringField('Name', [validators.Length(min=1, max=300), validators.DataRequired()])
    amount_paid = StringField('Amount Paid', [validators.DataRequired()])
    refund_status = RadioField('Refund Status', choices=[('Not Refunded', 'Not Refunded'), ('Refunded', 'Refunded')], validators=[DataRequired()])


