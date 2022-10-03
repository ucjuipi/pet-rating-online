from sqlalchemy import and_
from flask import session
from app import db
from sqlalchemy import Column, Integer, String, Text, Boolean
from flask_wtf import FlaskForm
from wtforms_sqlalchemy.fields import QuerySelectField
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from datetime import datetime


class user(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<user {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return user.query.get(int(id))


class research_group(db.Model):
    __tablename__ = "research_group"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    tag = db.Column(db.Text)
    description = db.Column(db.Text)

    def __repr__(self):
        return "<id= '%s', name= '%s', tag= '%s', description= '%s' >" % (self.id, self.name, self.tag, self.description)


class user_in_group (db.Model):
    __tablename__ = "user_in_group"
    __table_args__ = (
        db.PrimaryKeyConstraint('idgroup', 'iduser'),
    )

    idgroup = db.Column(
        db.Integer, db.ForeignKey('research_group.id'))
    iduser = db.Column(
        db.Integer, db.ForeignKey('user.id'))
    role = db.Column(db.Text)


class background_question(db.Model):
    __tablename__ = "background_question"
    idbackground_question = db.Column(db.Integer, primary_key=True)
    background_question = db.Column(db.String(120))
    answers = db.relationship(
        'background_question_answer', backref='question', lazy='dynamic')
    experiment_idexperiment = db.Column(db.Integer)

    def __repr__(self):
        return "<idbackground_question = '%s', background_question = '%s'>" % (self.idbackground_question, self.background_question)


class background_question_option(db.Model):
    __tablename__ = "background_question_option"
    idbackground_question_option = db.Column(db.Integer, primary_key=True)
    background_question_idbackground_question = db.Column(
        db.Integer, db.ForeignKey('background_question.idbackground_question'))
    option = db.Column(db.String(120))

    def __repr__(self):
        return "<idbackground_question_option = '%s', background_question_idbackground_question = '%s',  option = '%s'>" % (self.idbackground_question_option, self.background_question_idbackground_question, self.option)


class experiment (db.Model):
    __tablename__ = "experiment"
    idexperiment = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True)
    instruction = db.Column(db.Text, index=True)
    directoryname = db.Column(db.String(120), index=True, unique=True)
    language = db.Column(db.String(120))
    status = db.Column(db.String(120))
    randomization = db.Column(db.String(120))
    short_instruction = db.Column(db.Text, index=True)
    single_sentence_instruction = db.Column(db.Text, index=True)
    is_archived = db.Column(db.String(120))
    creator_name = db.Column(db.String(120))
    research_notification_filename = db.Column(db.String(120))
    creation_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    stimulus_size = db.Column(db.String(120))
    consent_text = db.Column(db.Text, index=True)
    use_forced_id = db.Column(db.String(120))
    embody_enabled = db.Column(db.Boolean, unique=False, default=False)

    group_id = db.Column(
        db.Integer, db.ForeignKey('research_group.id'))

    def __repr__(self):
        return "<idexperiment = '%s', name='%s', instruction='%s', directoryname='%s', language='%s', status='%s', randomization='%s', short_instruction='%s', single_sentence_instruction='%s', is_archived='%s', creator_name='%s', research_notification_filename='%s', creation_time='%s', stimulus_size='%s', consent_text='%s', use_forced_id='%s', embody_enabled='%s'>" % (self.idexperiment, self.name, self.instruction, self.directoryname, self.language, self.status, self.randomization, self.short_instruction, self.single_sentence_instruction, self.is_archived, self.creator_name, self.research_notification_filename, self.creation_time, self.stimulus_size, self.consent_text, self.use_forced_id, self.embody_enabled)


class answer_set (db.Model):
    __tablename__ = "answer_set"
    idanswer_set = db.Column(db.Integer, primary_key=True)
    experiment_idexperiment = db.Column(
        db.Integer, db.ForeignKey('experiment.idexperiment'))
    session = db.Column(db.String(120))
    agreement = db.Column(db.String(120))
    answer_counter = db.Column(db.Integer)
    answer_type = db.Column(db.String(120))
    registration_time = db.Column(
        db.DateTime, index=True, default=datetime.utcnow)
    last_answer_time = db.Column(
        db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return "<idanswer_set = '%s', experiment_idexperiment = '%s', session = '%s', agreement = '%s', answer_counter = '%s', registration_time = '%s', last_answer_time = '%s'>" % (self.idanswer_set, self.experiment_idexperiment, self.session, self.agreement, self.answer_counter, self.registration_time, self.last_answer_time)


class background_question_answer(db.Model):
    __tablename__ = "background_question_answer"
    idbackground_question_answer = db.Column(db.Integer, primary_key=True)
    answer_set_idanswer_set = db.Column(
        db.Integer, db.ForeignKey('answer_set.idanswer_set'))
    answer = db.Column(db.String(120))
    background_question_idbackground_question = db.Column(
        db.Integer, db.ForeignKey('background_question.idbackground_question'))

    def __repr__(self):
        return "<idbackground_question_answer = '%s', answer_set_idanswer_set = '%s', answer = '%s', background_question_idbackground_question = '%s'>" % (self.idbackground_question_answer, self.answer_set_idanswer_set, self.answer, self.background_question_idbackground_question)


def background_question_answer_query():
    return background_question_answer.query


"""
class ChoiceForm(FlaskForm):
    opts = QuerySelectField(query_factory=background_question_answer_query, allow_blank=True)

u = background_question.query.get(1)
vastaukset = u.answers.all()
## pitää sisällään kysymyksen 1 vastaukset
"""


class question (db.Model):
    __tablename__ = "question"
    idquestion = db.Column(db.Integer, primary_key=True)
    experiment_idexperiment = db.Column(
        db.Integer, db.ForeignKey('experiment.idexperiment'))
    question = db.Column(db.String(120))
    left = db.Column(db.String(120))
    right = db.Column(db.String(120))

    def __repr__(self):
        return "<idquestion = '%s', experiment_idexperiment = '%s', question = '%s', left = '%s', right = '%s'>" % (self.idquestion, self.experiment_idexperiment, self.question, self.left, self.right)


class embody_question (db.Model):
    __tablename__ = "embody_question"
    idembody = db.Column(db.Integer, primary_key=True)
    experiment_idexperiment = db.Column(
        db.Integer, db.ForeignKey('experiment.idexperiment'))
    picture = db.Column(db.Text)
    question = db.Column(db.Text)

    def __repr__(self):
        return "<idembody = '%s', experiment_idexperiment = '%s', picture = '%s', question = '%s'>" % (self.idembody, self.experiment_idexperiment, self.picture, self.question)


class page (db.Model):
    __tablename__ = "page"
    idpage = db.Column(db.Integer, primary_key=True)
    experiment_idexperiment = db.Column(
        db.Integer, db.ForeignKey('experiment.idexperiment'))
    type = db.Column(db.String(120), index=True)
    text = db.Column(db.Text)
    media = db.Column(db.String(120), index=True)

    def __repr__(self):
        return "<idpage = '%s', experiment_idexperiment = '%s', type = '%s', text = '%s', media = '%s'>" % (self.idpage, self.experiment_idexperiment, self.type, self.text, self.media)


class answer (db.Model):
    __tablename__ = "answer"
    idanswer = db.Column(db.Integer, primary_key=True)
    question_idquestion = db.Column(
        db.Integer, db.ForeignKey('question.idquestion'))
    answer_set_idanswer_set = db.Column(
        db.Integer, db.ForeignKey('answer_set.idanswer_set'))
    answer = db.Column(db.String(120))
    page_idpage = db.Column(db.Integer, db.ForeignKey('page.idpage'))

    def question(self):
        return int(self.question_idquestion)

    def result(self):
        return int(self.answer)

    def __repr__(self):
        return "<idanswer = '%s', question_idquestion = '%s', answer_set_idanswer_set = '%s', answer = '%s', page_idpage = '%s'>" % (self.idanswer, self.question_idquestion, self.answer_set_idanswer_set, self.answer, self.page_idpage)


class embody_answer (db.Model):
    __tablename__ = "embody_answer"
    idanswer = db.Column(db.Integer, primary_key=True)
    answer_set_idanswer_set = db.Column(
        db.Integer, db.ForeignKey('answer_set.idanswer_set'))
    page_idpage = db.Column(db.Integer, db.ForeignKey('page.idpage'))
    embody_question_idembody = db.Column(
        db.Integer, db.ForeignKey('embody_question.idembody'))
    coordinates = db.Column(db.Text)

    def question(self):
        return self.embody_question_idembody

    def result(self):
        return self.coordinates

    def __repr__(self):
        return "<idanswer = '%s', answer_set_idanswer_set = '%s', coordinates = '%s', page_idpage = '%s', embody_question_idembody='%s' >" % (self.idanswer, self.answer_set_idanswer_set, self.coordinates, self.page_idpage, self.embody_question_idembody)


class trial_randomization (db.Model):
    __tablename__ = "trial_randomization"
    idtrial_randomization = db.Column(db.Integer, primary_key=True)
    page_idpage = db.Column(db.Integer)
    randomized_idpage = db.Column(db.Integer)
    answer_set_idanswer_set = db.Column(db.Integer)
    experiment_idexperiment = db.Column(db.Integer)

    def __repr__(self):
        return "<idtrial_randomization = '%s', page_idpage = '%s', randomized_idpage = '%s', answer_set_idanswer_set = '%s', experiment_idexperiment = '%s'>" % (self.idtrial_randomization, self.page_idpage, self.randomized_idpage, self.answer_set_idanswer_set, self.experiment_idexperiment)

    @classmethod
    def get_randomized_page(cls, page_id):
        return cls.query.filter(and_(
            cls.answer_set_idanswer_set == session['answer_set'],
            cls.page_idpage == page_id)).first()


class forced_id (db.Model):
    __tablename__ = "forced_id"
    idforced_id = db.Column(db.Integer, primary_key=True)
    experiment_idexperiment = db.Column(
        db.Integer, db.ForeignKey('experiment.idexperiment'))
    pregenerated_id = db.Column(db.String(120))

    def __repr__(self):
        return "<idforced_id = '%s', experiment_idexperiment = '%s', pregenerated_id = '%s'>" % (self.idforced_id, self.experiment_idexperiment, self.pregenerated_id)
