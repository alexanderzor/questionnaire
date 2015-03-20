from flask import jsonify, render_template, redirect, url_for, flash, request, abort
from flask.ext.login import login_user, logout_user, login_required, current_user
from .forms import AskForm, AnswerForm, EditProfileForm
from ..models import User, Question, Answer
from . import main
from .. import db


@main.route('/', methods=['GET', 'POST'])
def index():
    users = User.query.all()
    if current_user.is_authenticated():
        query = current_user.followed_answers
        answers = query.order_by(Answer.timestamp.desc()).all()
    else:
        answers = []
    return render_template('index.html', answers=answers, users=users)


@main.route('/user/<username>', methods=['GET', 'POST'])
def user(username):
    form = AskForm()
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404)
    if form.validate_on_submit():
        question = Question(quest=form.ask.data, user_id=user.id)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('.user', username=username))
    answers = Answer.query.filter_by(user_id=user.id).order_by(Answer.timestamp.desc()).all()
    return render_template('user.html', form=form, user=user, answers=answers)


@main.route('/questions', methods=['GET', 'POST'])
@login_required
def questions():
    questions = current_user.questions.filter_by(answer=None).order_by(Question.timestamp.desc()).all()
    return render_template('questions.html', questions=questions)


@main.route('/answer/<question_id>', methods=['GET', 'POST'])
@login_required
def answer(question_id):
    form = AnswerForm()
    question = Question.query.filter_by(id=question_id).first()
    a = Answer.query.filter_by(question_id=question_id).first()
    if a:
        return redirect(url_for('.questions'))
    if form.validate_on_submit():
        answer = Answer(reply=form.answer.data, user_id=current_user.id, question_id=question_id)
        answer.reset()
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('.questions'))
    return render_template('answer.html', form=form, question=question)


@main.route('/vote/<answer_id>', methods=['GET', 'POST'])
@login_required
def vote(answer_id):
    answer = Answer.query.filter_by(id=answer_id).first()
    current_user.vote(answer)
    db.session.add(current_user)
    db.session.commit()
    return redirect(request.referrer or url_for('.user', username=answer.user.username))

@main.route('/unvote/<answer_id>', methods=['GET', 'POST'])
@login_required
def unvote(answer_id):
    answer = Answer.query.filter_by(id=answer_id).first()
    current_user.unvote(answer)
    db.session.add(current_user)
    db.session.commit()
    return redirect(request.referrer or url_for('.user', username=answer.user.username))


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('main.user', username=current_user.username))
    form.name.data = current_user.username
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    db.session.add(user)
    db.session.commit()
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    db.session.add(user)
    db.session.commit()
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    items = user.followers.all()
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', items=items, follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    items = user.followed.all()
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', items=items,
                           follows=follows)


@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500