from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
from app import db, login_manager
from datetime import datetime
import hashlib
from flask import request


class Votes(db.Model):
    __tablename__ = 'votes'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    questions = db.relationship('Question', backref='user', uselist=True, lazy='dynamic')
    answers = db.relationship('Answer', backref='user', uselist=True, lazy='dynamic')
    voted_answers = db.relationship('Votes', foreign_keys=[Votes.user_id],
                                    backref=db.backref('user', lazy='joined'), lazy='dynamic')
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'), lazy='dynamic',
                                cascade='all, delete-orphan')

    def vote(self, answer):
        if not self.has_voted(answer):
            f = Votes(user=self, answer=answer)
            db.session.add(f)

    def has_voted(self, answer):
        return self.voted_answers.filter_by(answer_id=answer.id).first() is not None

    def unvote(self, answer):
        f = self.voted_answers.filter_by(answer_id=answer.id).first()
        if f:
            db.session.delete(f)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_answers(self):
        return Answer.query.join(Follow, Follow.followed_id == Answer.user_id)\
            .filter(Follow.follower_id == self.id)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url,
                                                                     hash=hash,
                                                                     size=size,
                                                                     default=default,
                                                                     rating=rating)

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quest = db.Column(db.Text())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    '''user = db.relationship('User', backref='question', lazy='dynamic')'''
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    answer = db.relationship("Answer", uselist=False, backref="question")


class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    reply = db.Column(db.Text())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    '''user = db.relationship('User', backref='question', lazy='dynamic')'''
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    '''votes = db.Column(db.Integer)'''
    voters = db.relationship('Votes', foreign_keys=[Votes.answer_id],
                             backref=db.backref('answer', lazy='joined'), lazy='dynamic')

    def reset(self):
        self.votes = 0
        return self





@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))