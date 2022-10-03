import math
import json
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    session,
    flash,
    redirect,
    url_for,
    Blueprint
)
from flask_cors import CORS, cross_origin

from sqlalchemy import and_
from sqlalchemy import exc
from flask_babel import _, lazy_gettext as _l

from app import db
from app.models import experiment
from app.models import page, question
from app.models import answer_set, answer, embody_answer, embody_question
from app.models import user, trial_randomization
from app.forms import Answers, TaskForm, ContinueTaskForm, StringForm

task_blueprint = Blueprint("task", __name__,
                           template_folder='templates',
                           static_folder='static',
                           url_prefix='/task')


def get_randomized_page(page_id):
    """if trial randomization is on we will still use the same functionality that is used otherwise
    but we will pass the randomized pair of the page_id from trial randomization table to the task.html"""
    return trial_randomization.get_randomized_page(page_id)


def add_slider_answer(key, value, page_id=None):
    """Insert slider value to database. If trial randomization is set to 'Off' 
    the values are inputted for session['current_idpage']. Otherwise the values 
    are set for the corresponding id found in the trial randomization table"""

    participant_answer = answer(
        question_idquestion=key, answer_set_idanswer_set=session['answer_set'], answer=value, page_idpage=page_id)
    db.session.add(participant_answer)
    db.session.commit()


def update_answer_set_page():
    """Increment the page number by one in answer_set when user goes to next page"""
    the_time = datetime.now()
    the_time = the_time.replace(microsecond=0)

    update_answer_counter = answer_set.query.filter_by(
        idanswer_set=session['answer_set']).first()
    update_answer_counter.answer_counter = int(
        update_answer_counter.answer_counter) + 1
    update_answer_counter.last_answer_time = the_time
    db.session.commit()


def update_answer_set_type(answer_type):
    """If there are multiple question types(embody,slider,...) on one page, 
    then update the current question type"""
    the_time = datetime.now()
    the_time = the_time.replace(microsecond=0)

    updated_answer_set = answer_set.query.filter_by(
        idanswer_set=session['answer_set']).first()
    updated_answer_set.answer_type = answer_type
    updated_answer_set.last_answer_time = the_time
    db.session.commit()


def select_form_type():
    """Select form type based on the value in answer_set->answer_type"""

    form = None
    answer_set_type = answer_set.query.filter_by(
        idanswer_set=session['answer_set']).first().answer_type

    if answer_set_type == 'slider':
        form = TaskForm()

        # Get sliders from this experiment
        categories = question.query.filter_by(
            experiment_idexperiment=session['exp_id']).all()
        categories_and_scales = {}
        for cat in categories:
            scale_list = [(cat.left, cat.right)]
            categories_and_scales[cat.idquestion, cat.question] = scale_list
        form.categories1 = categories_and_scales
    else:
        form = StringForm()

    return form


def check_if_answer_exists(answer_type, page_id):
    """Check if there is already answer on certain experiment->page"""
    check_answer = None

    if answer_type == 'embody':
        check_answer = embody_answer.query.filter(and_(
            embody_answer.answer_set_idanswer_set == session['answer_set'], embody_answer.page_idpage == page_id)).first()
    elif answer_type == 'slider':
        check_answer = answer.query.filter(and_(
            answer.answer_set_idanswer_set == session['answer_set'], answer.page_idpage == page_id)).first()

    return check_answer


def next_page(pages):
    # If no more pages left -> complete task
    if not pages.has_next:
        return redirect(url_for('task.completed'))

    # If user has answered to all questions, then move to next page
    return redirect(url_for('task.task', page_num=pages.next_num))


def get_experiment_info():
    """Return experiment information from current session"""
    try:
        return experiment.query.filter_by(idexperiment=session['exp_id']).first()
    except KeyError as err:
        flash("No valid session found")
        return redirect('/')


def embody_on():
    """Check from session[exp_id] if embody questions are enabled"""
    experiment_info = get_experiment_info()
    if experiment_info.embody_enabled:
        return True
    else:
        return False


def slider_on():
    """Check from session[exp_id] if there are slider questions in this session"""
    experiment_info = get_experiment_info()
    questions = question.query.filter_by(
        experiment_idexperiment=experiment_info.idexperiment).all()

    if len(questions) == 0:
        return False
    return True


@task_blueprint.route('/embody/<int:page_num>', methods=['POST'])
@cross_origin()
def task_embody(page_num):
    '''Save embody drawing to database.'''

    form = StringForm(request.form)
    pages = page.query.filter_by(experiment_idexperiment=session['exp_id']).paginate(
        per_page=1, page=page_num, error_out=True)
    page_id = pages.items[0].idpage

    if form.validate():
        data = request.form.to_dict()
        coordinates = json.loads(data['coordinates'])

        # Check if randomization ON and if user has already answered to embody question
        if session['randomization'] == 'On':
            page_id = get_randomized_page(page_id).randomized_idpage

        check_answer = check_if_answer_exists('embody', page_id)

        # Add answer to DB
        if check_answer is None:
            for coordinate_data in coordinates:
                save_coordinates(coordinate_data, page_id)
        else:
            flash("Page has been answered already. Answers discarded")

    # Check if there are unanswered slider questions -> if true redirect to same page
    if slider_on():
        update_answer_set_type('slider')
        return redirect(url_for('task.task', page_num=page_num))

    update_answer_set_page()
    return next_page(pages)


def save_coordinates(coordinate_data, page_id):
    """All of the embody results from one page/stimulant is saved in this method"""
    idembody = int(coordinate_data['id'].split('-')[1])
    del coordinate_data['id']
    del coordinate_data['r']

    participant_answer = embody_answer(
        answer_set_idanswer_set=session['answer_set'], coordinates=json.dumps(coordinate_data), page_idpage=page_id, embody_question_idembody=idembody)
    db.session.add(participant_answer)
    db.session.commit()


@task_blueprint.route('/question/<int:page_num>', methods=['POST'])
def task_answer(page_num):
    '''Save slider answers to database'''

    form = TaskForm(request.form)
    pages = page.query.filter_by(experiment_idexperiment=session['exp_id']).paginate(
        per_page=1, page=page_num, error_out=True)
    page_id = pages.items[0].idpage

    if form.validate():

        # Check if randomization ON and if user has already answered to slider question
        if session['randomization'] == 'On':
            page_id = get_randomized_page(page_id).randomized_idpage

        check_answer = check_if_answer_exists('slider', page_id)

        if check_answer is None:
            data = request.form.to_dict()
            for key, value in data.items():
                add_slider_answer(key, value, page_id)
        else:
            flash("Page has been answered already. Answers discarded")

    if embody_on():
        update_answer_set_type('embody')

    # Always redirect to next page(stimulus) from sliders
    update_answer_set_page()
    return next_page(pages)


@task_blueprint.route('/<int:page_num>', methods=['GET'])
def task(page_num):
    """Get selected task page"""
    randomized_stimulus = ""
    experiment_info = get_experiment_info()

    # for text stimuli the size needs to be calculated since the template element utilises h1-h6 tags.
    # A value of stimulus size 12 gives h1 and value of 1 gives h6
    stimulus_size = experiment_info.stimulus_size
    stimulus_size_text = 7-math.ceil((int(stimulus_size)/2))

    pages = page.query.filter_by(experiment_idexperiment=session['exp_id']).paginate(
        per_page=1, page=page_num, error_out=True)
    page_id = pages.items[0].idpage
    progress_bar_percentage = round((pages.page/pages.pages)*100)
    session['current_idpage'] = page_id

    # if trial randomization is on we will still use the same functionality that is used otherwise
    # but we will pass the randomized pair of the page_id from trial randomization table to the task.html
    if session['randomization'] == 'On':
        randomized_page_id = get_randomized_page(page_id).randomized_idpage
        randomized_stimulus = page.query.filter_by(
            idpage=randomized_page_id).first()

    # get all embody questions
    embody_questions = embody_question.query.filter_by(
        experiment_idexperiment=session['exp_id']).all()

    return render_template(
        'task.html',
        pages=pages,
        page_num=page_num,
        progress_bar_percentage=progress_bar_percentage,
        form=select_form_type(),
        randomized_stimulus=randomized_stimulus,
        rating_instruction=experiment_info.single_sentence_instruction,
        stimulus_size=stimulus_size,
        stimulus_size_text=stimulus_size_text,
        experiment_info=experiment_info,
        embody_questions=embody_questions
    )


@task_blueprint.route('/completed')
def completed():
    session.pop('user', None)
    session.pop('exp_id', None)
    session.pop('agree', None)
    session.pop('answer_set', None)
    session.pop('type', None)
    session.pop('randomization', None)

    return render_template('task_completed.html')


@task_blueprint.route('/continue', methods=['GET', 'POST'])
def continue_task():
    """Continue unfinished task"""

    # Set experience if to session
    exp_id = request.args.get('exp_id', None)
    session['exp_id'] = exp_id

    form = ContinueTaskForm()

    if form.validate_on_submit():
        # check if participant ID is found from db and that the answer set is linked to the correct experiment
        participant = answer_set.query.filter(and_(
            answer_set.session == form.participant_id.data, answer_set.experiment_idexperiment == exp_id)).first()
        if participant is None:
            flash('Invalid ID')
            return redirect(url_for('task.continue_task', exp_id=exp_id))

        # if correct participant_id is found with the correct experiment ID; start session for that user
        exp = get_experiment_info()
        session['user'] = form.participant_id.data
        session['answer_set'] = participant.idanswer_set
        session['randomization'] = exp.randomization

        update_answer_set_type(participant.answer_type)

        mediatype = page.query.filter_by(
            experiment_idexperiment=session['exp_id']).first()
        if mediatype:
            session['type'] = mediatype.type
        else:
            flash('No pages or mediatype set for experiment')
            return redirect('/')

        # If participant has done just the registration redirect to the first page of the experiment
        if participant.answer_counter == 0:
            return redirect(url_for('task.task', page_num=1))

        redirect_to_page = participant.answer_counter + 1
        experiment_page_count = db.session.query(page).filter_by(
            experiment_idexperiment=session['exp_id']).count()

        # If participant has ansvered all pages allready redirect to task completed page
        if experiment_page_count == participant.answer_counter:
            return redirect(url_for('task.completed'))

        return redirect(url_for('task.task', page_num=redirect_to_page))

    return render_template('continue_task.html', exp_id=exp_id, form=form)


@task_blueprint.route('/quit')
def quit():

    user_id = session['user']
    session.pop('user', None)
    session.pop('exp_id', None)
    session.pop('agree', None)
    session.pop('answer_set', None)
    session.pop('type', None)

    return render_template('quit_task.html', user_id=user_id)


# EOF
