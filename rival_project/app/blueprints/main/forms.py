from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, URL, Optional, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class FeedbackForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Feedback')

class CompanyForm(FlaskForm):
    name = StringField('Company name', validators=[Optional(), Length(max=200)])
    url = StringField('Website URL', validators=[Optional(), URL(require_tld=False, message='Invalid URL')])
    add_to_watchlist = BooleanField('Add to my watchlist', default=True)
    submit = SubmitField('Add Company')

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators=extra_validators)
        if not ok:
            return False
        # At least one of name or url must be provided
        name = (self.name.data or '').strip()
        url = (self.url.data or '').strip()
        if not name and not url:
            self.name.errors.append('Provide a company name or a website URL.')
            self.url.errors.append('Provide a company name or a website URL.')
            return False
        return True


class QuickAddForm(FlaskForm):
    url = StringField('Company URL', validators=[DataRequired(message='Provide a URL'), URL(require_tld=False, message='Invalid URL')])
    add_to_watchlist = BooleanField('Add to my watchlist', default=True)
    submit = SubmitField('Add')


class TickerForm(FlaskForm):
    ticker = StringField('Ticker', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Save ticker')