from app import app, db, babel
from app.models import background_question, background_question_option
from app.models import experiment
from app.models import answer_set
from app.models import background_question_answer
from app.models import question, page, answer
from app.models import user, trial_randomization, forced_id



@app.shell_context_processor
def make_shell_context():
    return {'db': db, 
            'background_question': background_question,
            'background_question_option': background_question_option,
            'experiment': experiment,
            'answer_set': answer_set,
            'background_question_answer': background_question_answer,
            'question': question,
            'page': page,
            'answer': answer,
            'user': user,
            'trial_randomization': trial_randomization,
            'forced_id': forced_id
            }



"""

from app import app, db
from app.models import Background_question, Background_question_answer
from app.models import Experiment, Question, Answer_set
from app.models import Page, Answer

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 
            'Background_question': Background_question,
            'Background_question_answer': Background_question_answer,
            'Experiment': Experiment,
            'Question': Question,
            'Answer_set': Answer_set,
            'Page': Page,
            'Answer': Answer,
            }
"""