#!/usr/bin/env python

"""
Visualize emBODY data

This python script is based on matlab code found from:
https://version.aalto.fi/gitlab/eglerean/embody/tree/master/matlab
"""

from config import Config
from app import socketio, app
from flask_socketio import emit
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import time
import datetime
import json
import mysql.connector as mariadb
import argparse

import numpy as np
import scipy.ndimage as ndimage

import matplotlib
matplotlib.use('agg')


# Hard coded image size for default embody image
WIDTH = 207
HEIGHT = 600

# image paths
DEFAULT_IMAGE_PATH = './app/static/img/dummy_600.png'
IMAGE_PATH_MASK = './app/static/img/dummy_600_mask.png'
STATIC_PATH = './app/static/embody_drawings/'

# Interpolation methods
METHODS = ['none', 'bilinear', 'bicubic', 'gaussian']

# SELECT methods
SELECT_ALL = ("SELECT coordinates from embody_answer")
SELECT_BY_EXP_ID = 'select coordinates from embody_answer as em JOIN (SELECT idanswer_set FROM answer_set as a JOIN experiment as e ON a.experiment_idexperiment=e.idexperiment AND e.idexperiment=%s) as ida ON em.answer_set_idanswer_set=ida.idanswer_set'
SELECT_BY_ANSWER_SET = 'select coordinates from embody_answer WHERE answer_set_idanswer_set=%s'
SELECT_BY_PAGE = 'select coordinates from embody_answer WHERE page_idpage=%s'
SELECT_BY_PAGE_AND_PICTURE = 'select coordinates from embody_answer where page_idpage=%s and embody_question_idembody=%s'

# Get date
now = datetime.datetime.now()
DATE_STRING = now.strftime("%Y-%m-%d")


class MyDB(object):

    def __init__(self):
        self._db_connection = mariadb.connect(
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            host=Config.MYSQL_SERVER,
            auth_plugin='mysql_native_password'
        )
        self._db_cur = self._db_connection.cursor()

    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def __del__(self):
        self._db_connection.close()


def matlab_style_gauss2D(shape=(1, 1), sigma=5):
    """2D gaussian mask - should give the same result as MATLAB's
    fspecial('gaussian',[shape],[sigma])"""

    m, n = [(ss-1.)/2. for ss in shape]
    y, x = np.ogrid[-m:m+1, -n:n+1]
    h = np.exp(-(x*x + y*y) / (2.*sigma*sigma))
    h[h < np.finfo(h.dtype).eps*h.max()] = 0
    sumh = h.sum()
    if sumh != 0:
        h /= sumh
    return h


def map_coordinates(a, b, c=None):
    return [a, b, c]


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' %
                  (method.__name__, (te - ts) * 1000))
        return result

    return timed


@timeit
def get_coordinates(idpage, idembody=None, select_clause=SELECT_BY_PAGE_AND_PICTURE):
    """Select all drawn points from certain stimulus and plot them onto 
    the human body"""

    # init db
    db = MyDB()
    db.query(select_clause, (idpage, idembody))

    # Get coordinates
    coordinates = format_coordinates(db._db_cur)

    if idembody:
        # Get image path
        image_query = db.query(
            'SELECT picture from embody_question where idembody=%s', (idembody,))
        image_path = db._db_cur.fetchone()[0]
        image_path = './app' + image_path

        # Draw image
        plt = plot_coordinates(coordinates, image_path)
    else:
        plt = plot_coordinates(coordinates, DEFAULT_IMAGE_PATH)

    # close db connection
    db.__del__()

    # Save image to ./app/static/
    img_filename = 'PAGE-' + str(idpage) + '-' + DATE_STRING + '.png'
    plt.savefig(STATIC_PATH + img_filename)

    # Return image path to function caller
    return img_filename


def format_coordinates(cursor):
    # Init coordinate arrays and radius of point
    x = []
    y = []
    r = []
    standard_radius = 13

    # Loop through all of the saved coordinates and push them to coordinates arrays
    for coordinate in cursor:

        try:
            coordinates = json.loads(coordinate[0])
            x.extend(coordinates['x'])
            y.extend(coordinates['y'])
            r.extend(coordinates['r'])
        except KeyError:
            standard_radiuses = np.full(
                (1, len(coordinates['x'])), standard_radius).tolist()[0]
            r.extend(standard_radiuses)
            continue
        except ValueError as err:
            app.logger.info(err)
            continue

    return {
        "x": x,
        "y": y,
        "coordinates": list(map(map_coordinates, x, y, r))
    }


def plot_coordinates(coordinates, image_path=DEFAULT_IMAGE_PATH):

    # Total amount of points
    points_count = len(coordinates['coordinates'])
    step = 1

    # Load image to a plot
    image = mpimg.imread(image_path)
    image_data = image.shape

    # Init plots
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)

    # Draw circles from coordinates (imshow don't need interpolation)
    # TODO: set sigma according to brush size!
    ax2.set_title("gaussian disk around points / raw image")

    # set height/width from image
    frame = np.zeros((image_data[0] + 10, image_data[1] + 10))

    if image_path == DEFAULT_IMAGE_PATH:
        # app.logger.info(coordinates)

        for idx, point in enumerate(coordinates["coordinates"]):

            try:
                frame[int(point[1]), int(point[0])] = 1
            except IndexError as err:
                app.logger.info(err)

            # Try to send progress information to socket.io
            if idx == 0:
                continue

            if round((idx / points_count) * 100) % (step * 5) == 0:
                try:
                    emit('progress', {'done': step * 5, 'from': 100})
                    socketio.sleep(0.05)
                except RuntimeError:
                    continue

                step += 1

        point = ndimage.gaussian_filter(frame, sigma=5)
        ax2.imshow(point, cmap='hot', interpolation='none')

        image_mask = mpimg.imread(IMAGE_PATH_MASK)
        ax2.imshow(image_mask)

    else:
        # TODO: gaussian disk appearing only on empty spaces in the pictures
        # -> at the moment this implementation works only for the default image
        # with pre-created image mask (IMAGE_PATH_MASK)
        ax2.imshow(image)

    # Plot coordinates as points
    ax1.set_title("raw points")
    ax1.plot(coordinates["x"], coordinates["y"], 'ro', alpha=0.2)
    ax1.imshow(image, alpha=0.6)

    app.logger.info("image plotted")

    # return figure for saving/etc...
    return fig


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser(
        description='Draw bodily maps of emotions')
    arg_parser.add_argument(
        '-s', '--stimulus', help='Select drawn points from certain stimulus', required=False, action='store_true')
    arg_parser.add_argument(
        '-e', '--experiment', help='Select drawn points from certain experiment', required=False, action='store_true')
    arg_parser.add_argument(
        '-a', '--answer-set', help='Select drawn points from certain answer_set', required=False, action='store_true')
    arg_parser.add_argument('integers', metavar='N', type=int,
                            nargs='+', help='an integer for the accumulator')
    args = vars(arg_parser.parse_args())
    value = args['integers'][0]

    if args['stimulus']:
        get_coordinates(value, None, SELECT_BY_PAGE)
    elif args['experiment']:
        get_coordinates(value, None, SELECT_BY_EXP_ID)
    elif args['answer_set']:
        get_coordinates(value, None, SELECT_BY_EXP_ID)
    else:
        print("No arguments given. Exit.")
