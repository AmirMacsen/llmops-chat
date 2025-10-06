from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class CompletionRequest(FlaskForm):
    query = StringField('query', validators=[
        DataRequired(message='Query is required'),
        Length(min=1, max=2000, message='Query length must be between 1 and 2000')
    ])
