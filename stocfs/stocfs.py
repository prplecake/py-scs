from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from stocfs.auth import login_required
from stocfs.db import get_db


bp = Blueprint('stocfs', __name__)

@bp.route('/')
def index():
    db = get_db()
    data = db.execute(
        'SELECT i.id, name, description, url FROM item i'
        ' ORDER BY name ASC'
    ).fetchall()
    return render_template('stocfs/index.html', data=data)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        url = request.form['url']
        error = None

        if not name:
            error = 'The name is required.'

        if error is not None:
            falsh(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO item (name, description, url)'
                ' VALUES (?, ?, ?)',
                (name, description, url)
            )
            db.commit()
            return redirect(url_for('index'))

    return render_template('stocfs/create.html')

def get_item(id):
    item = get_db().execute(
        'SELECT i.id, name, description, url'
        ' FROM item i WHERE i.id = ?',
        (id,)
    ).fetchone()

    if item is None:
        abort(404, "Item {0} doesn't exist.".format(id))

    return item


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    item = get_item(id)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        url = request.form['url']
        error = None

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE item SET name = ?, description = ?, url = ?'
                ' WHERE id = ?',
                (name, description, url, id)
            )
            db.commit()
            return redirect(url_for('index'))

    return render_template('stocfs/update.html', item=item)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_item(id)
    db = get_db()
    db.execute('DELETE FROM item WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('index'))
