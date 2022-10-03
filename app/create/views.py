import os
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

from flask_login import login_required

from app.routes import APP_ROOT
from app import app, db
from app.models import background_question, experiment, background_question_answer, page, question, background_question_option, answer_set, answer, forced_id, user, trial_randomization, research_group, user_in_group
from app.forms import (
    CreateExperimentForm, CreateBackgroundQuestionForm,
    CreateQuestionForm, UploadStimuliForm
)

create_blueprint = Blueprint("create", __name__,
                             template_folder='templates',
                             # static_folder='static',
                             url_prefix='/create')


@create_blueprint.route('/experiment', methods=['GET', 'POST'])
@login_required
def create_experiment():

    form = CreateExperimentForm(request.form)

    user_groups = user_in_group.query.filter_by(
        iduser=session['user_id']).all()

    if user_groups:
        user_groups = [ug.idgroup for ug in user_groups]

        valid_groups = research_group.query.filter(
            research_group.id.in_(user_groups)).all()

    else:
        valid_groups = []

    if request.method == 'POST' and form.validate():

        the_time = datetime.now()
        the_time = the_time.replace(microsecond=0)

        new_exp = experiment(name=request.form['name'], instruction=request.form['instruction'], language=request.form['language'], status='Hidden', randomization='Off', single_sentence_instruction=request.form['single_sentence_instruction'],
                             short_instruction=request.form['short_instruction'], creator_name=request.form['creator_name'], is_archived='False', creation_time=the_time, stimulus_size='7', consent_text=request.form['consent_text'], use_forced_id='Off', group_id=request.form['group'])
        db.session.add(new_exp)
        db.session.commit()
        exp_id = new_exp.idexperiment

        return redirect(url_for('create.experiment_bgquestions', exp_id=exp_id))

    return render_template('create_experiment.html', form=form, valid_groups=valid_groups)


@create_blueprint.route('/experiment_bgquestions', methods=['GET', 'POST'])
@login_required
def experiment_bgquestions():

    exp_id = request.args.get('exp_id', None)
    form = CreateBackgroundQuestionForm(request.form)

    if request.method == 'POST' and form.validate():
        str = form.bg_questions_and_options.data

        # Split the form data into a list that separates questions followed by the corresponding options
        str_list = str.split('/n')

        # Iterate through the questions and options list
        for a in range(len(str_list)):

            # Split the list cells further into questions and options
            list = str_list[a].split(';')

            # Input the first item of the list as a question in db and the items followed by that as options for that question
            for x in range(len(list)):

                if x == 0:
                    add_bgquestion = background_question(
                        background_question=list[x], experiment_idexperiment=exp_id)
                    db.session.add(add_bgquestion)
                    db.session.commit()

                else:
                    add_bgq_option = background_question_option(
                        background_question_idbackground_question=add_bgquestion.idbackground_question, option=list[x])
                    db.session.add(add_bgq_option)
                    db.session.commit()

        return redirect(url_for('create.experiment_questions', exp_id=exp_id))

    return render_template('create_experiment_bgquestions.html', form=form, exp_id=exp_id)


@create_blueprint.route('/experiment_questions', methods=['GET', 'POST'])
@login_required
def experiment_questions():
    """Add slider questions"""

    exp_id = request.args.get('exp_id', None)
    form = CreateQuestionForm(request.form)

    if request.method == 'POST':

        str = form.questions_and_options.data
        str_list = str.split('/n')

        for a in range(len(str_list)):

            list = str_list[a].split(';')

            # If there are the wrong amount of values for any of the the slider input values
            # redirect back to the form
            if len(list) != 3:

                flash(
                    "Error Each slider must have 3 parameters separated by ; Some slider has:")
                flash(len(list))

                return redirect(url_for('create.experiment_questions', exp_id=exp_id))

        # If all the slider inputs were of length 3 items
        # we can input them to db
        for a in range(len(str_list)):

            list = str_list[a].split(';')

            add_question = question(
                experiment_idexperiment=exp_id, question=list[0], left=list[1], right=list[2])
            db.session.add(add_question)
            db.session.commit()

    return redirect(url_for('create.experiment_upload_stimuli', exp_id=exp_id))


@create_blueprint.route('/experiment_upload_stimuli', methods=['GET', 'POST'])
@login_required
def experiment_upload_stimuli():
    """Upload stimuli"""

    exp_id = request.args.get('exp_id', None)
    form = UploadStimuliForm(request.form)

    if request.method == 'POST' and form.validate():

        # If stimulus type is text lets parse the information and insert it to database
        if form.type.data == 'text':
            string = form.text.data
            str_list = string.split('/n')

            for a in range(len(str_list)):
                add_text_stimulus = page(
                    experiment_idexperiment=exp_id, type='text', text=str_list[a], media='none')
                db.session.add(add_text_stimulus)
                db.session.commit()

            return redirect(url_for('experiment.view', exp_id=exp_id))

        else:
            # Upload stimuli into /static/experiment_stimuli/exp_id folder
            # Create the pages for the stimuli by inserting experiment_id, stimulus type, text and names of the stimulus files (as a path to the folder)

            path = 'static/experiment_stimuli/' + str(exp_id)
            target = os.path.join(APP_ROOT, path)

            if not os.path.isdir(target):
                os.mkdir(target)

            # This returns a list of filenames: request.files.getlist("file")
            for file in request.files.getlist("file"):

                # save files in the correct folder
                filename = file.filename
                destination = "/".join([target, filename])
                file.save(destination)

                # add pages to the db
                db_path = path + str('/') + str(filename)
                new_page = page(experiment_idexperiment=exp_id,
                                type=form.type.data, media=db_path)

                db.session.add(new_page)
                db.session.commit()

                # flash("Succes!")

            return redirect(url_for('experiment.view', exp_id=exp_id))

        return redirect(url_for('create.experiment_upload_stimuli', exp_id=exp_id))

    return render_template('create_experiment_upload_stimuli.html', form=form)
