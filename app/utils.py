import os
import tempfile
import time
import json
from itertools import zip_longest
import concurrent.futures
from flask import send_file
from flask_socketio import emit
from app import app
from app.models import background_question, background_question_answer, \
    page, question, answer_set, answer, embody_answer, embody_question


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            app.logger.info('{} {:2.2f} ms'.format(
                method.__name__, (te - ts) * 1000))
        return result

    return timed


def map_values_to_int(values: dict):
    #values = [map(int, i) for i in list(values.values())]
    return zip_longest(*values.values(), fillvalue=None)


def calculate_mean(values: list) -> float:
    n_answers = sum(x is not None for x in values)
    sum_of_answers = float(sum(filter(None, values)))
    mean = sum_of_answers / n_answers
    return round(mean, 2)


def get_mean_from_slider_answers(answers):
    return [calculate_mean(values) for values in map_values_to_int(answers)]


def saved_data_as_file(filename, data):
    """write CSV data to temporary file on host and send that file
    to requestor"""
    try:
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(data)
            tmp.flush()
            return send_file(path,
                             mimetype='text/csv',
                             as_attachment=True,
                             attachment_filename=filename)
    finally:
        os.remove(path)


def get_values_from_list_of_answers(page_question, answers):
    page_id = page_question[0]
    question_id = page_question[1]
    for _answer in answers:
        try:
            if _answer.question_idquestion == question_id and \
                    _answer.page_idpage == page_id:
                return int(_answer.answer)
        except AttributeError:
            if _answer.embody_question_idembody == question_id and \
                    _answer.page_idpage == page_id:
                return _answer
    return None


def question_matches_answer(question, answer):
    if (answer.page_idpage == question[0] and answer.question() == question[1]):
        return True
    return False


def map_answers_to_questions(answers, questions):
    '''
    questions = [(4, 1), (4, 2), (5, 1), (5, 2), (6, 1), (6, 2)]
    +
    answers = [{p:6, q:1, a:100}, {p:6, q:2, a:99}]
    ->
    partial_answer = [None, None, None, None, 100, 99]
    '''

    # results = []
    results = list(map(lambda x: None, questions))

    nth_answer = 0

    for nth_question, question in enumerate(questions):

        try:
            current_answer = answers[nth_answer]
        except IndexError:
            break

        if question_matches_answer(question, current_answer):
            results[nth_question] = current_answer.result()
            nth_answer += 1

    return results


@timeit
def generate_csv(exp_id, file_handle):

    # answer sets with participant ids
    participants = answer_set.query.filter_by(
        experiment_idexperiment=exp_id).all()

    # pages aka stimulants
    pages = page.query.filter_by(experiment_idexperiment=exp_id).all()

    # background questions
    bg_questions = background_question.query.filter_by(
        experiment_idexperiment=exp_id).all()

    # question
    questions = question.query.filter_by(experiment_idexperiment=exp_id).all()

    # embody questions
    embody_questions = embody_question.query.filter_by(
        experiment_idexperiment=exp_id).all()

    # create CSV-header
    header = 'participant id;'
    header += ';'.join([str(count) + '. bg_question: ' + q.background_question.strip()
                        for count, q in enumerate(bg_questions, 1)])

    for idx in range(1, len(pages) + 1):
        if len(questions) > 0:
            header += ';' + ';'.join(['page' + str(idx) + '_' + str(count) + '. slider_question: ' +
                                      question.question.strip() for count, question in enumerate(questions, 1)])

    for idx in range(1, len(pages) + 1):
        if len(embody_questions) > 0:
            header += ';' + ';'.join(['page' + str(idx) + '_' + str(count) + '. embody_question: ' +
                                      question.picture.strip() for count, question in enumerate(embody_questions, 1)])

    file_handle.write(header + '\r\n')

    # filter empty answer_sets
    participants = list(filter(lambda participant: True if int(
        participant.answer_counter) > 0 else False, participants))

    len_participants = len(participants)

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Start the load operations and mark each future with its URL
        future_to_answer = {
            executor.submit(generate_answer_row, participant, pages, questions, embody_questions): participant
            for participant in participants}

        for nth, future in enumerate(concurrent.futures.as_completed(future_to_answer)):
            # for testing purpose
            # answer_row = future_to_answer[future]
            try:
                emit('progress', {'done': nth, 'from': len_participants})
                data = future.result()
                file_handle.write(data + '\n')
                # to ensure that all internal buffers associated with fd are written to disk
                file_handle.flush()
            except Exception as exc:
                print('generated an exception: {}'.format(exc))
                # return False
    
    return True


def generate_answer_row(participant, pages, questions, embody_questions):

    with app.app_context():

        answer_row = ''

        # append user session id
        answer_row += participant.session + ';'

        # append background question answers
        bg_answers = background_question_answer.query.filter_by(
            answer_set_idanswer_set=participant.idanswer_set).all()
        bg_answers_list = [str(a.answer).strip() for a in bg_answers]
        answer_row += ';'.join(bg_answers_list) + ';'

        # append slider answers
        slider_answers = answer.query.filter_by(
            answer_set_idanswer_set=participant.idanswer_set) \
            .order_by(answer.page_idpage, answer.question_idquestion) \
            .all()

        pages_and_questions = {}

        for p in pages:
            questions_list = [(p.idpage, a.idquestion) for a in questions]
            pages_and_questions[p.idpage] = questions_list

        _questions = [
            item for sublist in pages_and_questions.values() for item in sublist]

        answers_list = map_answers_to_questions(slider_answers, _questions)

        # typecast elemnts to string
        answers_list = [str(a).strip() for a in answers_list]

        answer_row += ';'.join(answers_list) + \
            ';' if slider_answers else len(
                questions) * len(pages) * ';'

        # append embody answers (coordinates)
        # save embody answers as bitmap images
        embody_answers = embody_answer.query.filter_by(
            answer_set_idanswer_set=participant.idanswer_set) \
            .order_by(embody_answer.page_idpage) \
            .all()

        pages_and_questions = {}

        for p in pages:
            questions_list = [(p.idpage, a.idembody) for a in embody_questions]
            pages_and_questions[p.idpage] = questions_list

        _questions = [
            item for sublist in pages_and_questions.values() for item in sublist]

        _embody_answers = map_answers_to_questions(embody_answers, _questions)

        answers_list = []

        for answer_data in _embody_answers:
            if not answer_data:
                answers_list.append('')
                continue

            try:
                coordinates = json.loads(answer_data)
                em_height = coordinates.get('height', 600) + 2
                em_width = coordinates.get('width', 200) + 2

                coordinates_to_bitmap = [
                    [0 for x in range(em_height)] for y in range(em_width)]

                coordinates = list(
                    zip(coordinates.get('x'), coordinates.get('y')))

                for point in coordinates:

                    try:
                        # for every brush stroke, increment the pixel
                        # value for every brush stroke
                        coordinates_to_bitmap[int(
                            point[0])][int(point[1])] += 0.1
                    except IndexError:
                        continue

                answers_list.append(json.dumps(coordinates_to_bitmap))

            except ValueError as err:
                print(err)
                #app.logger(err)

        answer_row += ';'.join(answers_list) if embody_answers else \
            len(embody_questions) * len(pages) * ';'

        return answer_row
