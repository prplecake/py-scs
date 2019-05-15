from flask import (
    Blueprint, flash, g, redirect,
    render_template, request, url_for
)
from werkzeug.exceptions import abort

from scs.auth import login_required
from scs.db import get_db


bp = Blueprint('scs', __name__)


@bp.route('/')
def index():
    db = get_db()
    data = db.execute(
        'SELECT i.id, name, description, url FROM item i'
        ' ORDER BY name ASC'
    ).fetchall()
    return render_template('scs/index.html', data=data)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        url = request.form['url']
        tag_string = request.form['tags']
        error = None

        tags = [x.strip() for x in filter(None, tag_string.split(','))]

        if not name:
            error = 'The name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO item (name, description, url)'
                ' VALUES (?, ?, ?)',
                (name, description, url)
            )
            itemId = cur.lastrowid
            tag_ids = []
            for tag in tags:
                cur.execute(
                    'INSERT OR IGNORE INTO tag (name) VALUES (?)', (tag,)
                )
                # tag_ids.append(cur.lastrowid)
                tag_ids.append(cur.execute(
                    'SELECT id FROM tag WHERE (name) IN (?)',
                    (tag,)
                ).fetchone()['id'])
            print(tag_ids)
            for tagId in tag_ids:
                cur.execute(
                    'INSERT OR IGNORE INTO itemtag (item_id, tag_id)'
                    ' VALUES (?, ?)',
                    (itemId, tagId)
                )
            db.commit()
            return redirect(url_for('index'))

    return render_template('scs/create.html')


def get_item(id):
    item = get_db().execute(
        'SELECT i.id, name, description, url'
        ' FROM item i WHERE i.id = ?',
        (id,)
    ).fetchone()

    if item is None:
        abort(404, "Item {0} doesn't exist.".format(id))

    return item


def get_item_tags(item_id):
    tag_ids = get_db().execute(
        'SELECT tag_id FROM itemtag WHERE item_id = ?',
        (item_id,)
    ).fetchall()
    tagIds = [x['tag_id'] for x in tag_ids]
    tags = []
    for tagId in tagIds:
        tags.append(get_db().execute(
            'SELECT * FROM tag WHERE id = ?',
            (tagId,)
        ).fetchone()['name'])

    return tags


def get_all_tags():
    tags = get_db().execute(
        'SELECT * FROM tag'
    ).fetchall()

    if tags is None:
        abort(404, "No tags.")

    return tags


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    item = get_item(id)
    tags = ', '.join(get_item_tags(id))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        url = request.form['url']
        tags = request.form['tags']
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

    return render_template(
        'scs/update.html',
        item=item, tags=tags
    )


@bp.route('/tags')
@bp.route('/tags/<int:id>')
def view_tagsid(id=None):
    if id:
        tags = get_item_tags(id)
    else:
        tags = [x['name'] for x in get_all_tags()]

    return render_template('scs/tags.html', tags=tags)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_item(id)
    db = get_db()
    db.execute('DELETE FROM item WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('index'))
