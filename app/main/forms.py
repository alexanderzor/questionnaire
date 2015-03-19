from flask.ext.wtf import Form
from wtforms.fields import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Length


class AskForm(Form):
    ask = TextAreaField('Ask a question:', validators=[DataRequired()])
    submit = SubmitField('Ask')


class AnswerForm(Form):
    answer = TextAreaField('Answer:', validators=[DataRequired()])
    submit = SubmitField('Answer a question')


class EditProfileForm(Form):
    name = StringField('Real name:', validators=[Length(0, 64)])
    location = StringField('Location:', validators=[Length(0, 64)])
    about_me = TextAreaField('About me:')
    submit = SubmitField('Submit')