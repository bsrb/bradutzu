import bcrypt
from datetime import datetime
from flask import abort, Blueprint, render_template, redirect, request, send_from_directory
import hashlib
import os
import pytz
from uuid import uuid4

from brad.extensions import ctrl, db 
from brad.models.user import Animation, User
from brad.controller import safe_run
from config import Config

main = Blueprint('main', __name__)

def get_user(cookie):
    if cookie is None:
        return None
    user = User.query.filter_by(auth=cookie).first()
    # user is None if not found
    return user

def get_currently_playing():
    if ctrl.CTRL_IS_TESTING:
        return f'{ctrl.ANIMATION_TEST_USER} is testing'
    if ctrl.ANIMATION_FILENAME.endswith('.py'):
        filename = ctrl.ANIMATION_FILENAME[:-3]
    else:
        return f'ERROR: invalid animation file name - {filename}'
    anim = Animation.query.filter_by(id=filename).first()
    if anim == None:
        if filename == 'default':
            return 'default animation'
        else:
            return 'animation was deleted :kekbye'
    return f'"{anim.name}" by {anim.owner}'

@main.route('/')
def index():
    user = get_user(request.cookies.get('auth'))
    if user is None:
        return render_template('index.html', first_button_href='login', first_button_text='LOGIN',
                               second_button_href='register', second_button_text='REGISTER',
                               currently_playing=get_currently_playing())

    anims = Animation.query.filter_by(owner=user.username).all()
    animations = {}
    for an in anims:
        animations[an.id] = {}
        animations[an.id]['name'] = an.name
        animations[an.id]['id'] = an.id

    return render_template('index.html', first_button_href='', first_button_text=user.username.upper(),
                            second_button_href='logout', second_button_text='LOGOUT',
                            animations=animations, currently_playing=get_currently_playing())

@main.route('/login', methods = ['GET', 'POST'])
def login():
    user = get_user(request.cookies.get('auth'))
    if user is not None:
        return redirect('/')

    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json()
    for i in ['username', 'password']:
        if i not in data:
            return { 'success': False }

    user = User.query.filter_by(username=data['username']).first()
    if user is None:
        return { 'success': False }

    pwd = data['password']
    if isinstance(pwd, str):
        pwd = pwd.encode('utf-8')
    if not bcrypt.checkpw(pwd, user.password):
        return { 'success': False }

    auth = uuid4().hex
    user.auth = auth
    db.session.commit()
    return { 'success': True, 'auth': auth }

def valid_secret(data):
    username = data['username']
    if isinstance(username, str):
        username = username.encode('utf-8')
    client_secret = data['secret']
    if isinstance(client_secret, str):
        client_secret = client_secret.encode('utf-8')

    secret = os.environ.get('REGISTER_SECRET')
    if isinstance(secret, str):
        secret = secret.encode('utf-8')

    hash = hashlib.sha256(username + secret).hexdigest().encode('utf-8')
    if hash == client_secret:
        return True
    return False

@main.route('/register', methods = ['GET', 'POST'])
def register():
    user = get_user(request.cookies.get('auth'))
    if user is not None:
        return redirect('/')

    if request.method == 'GET':
        return render_template('register.html')

    data = request.get_json()
    for i in ['username', 'password', 'secret']:
        if i not in data:
            return { 'success': False , 'message': 'missing parameters!' }

    if not valid_secret(data):
        return { 'success': False , 'message': 'invalid secret!' }

    pwd = data['password']
    if isinstance(pwd, str):
        pwd = pwd.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(pwd, salt)

    username = data['username'].lower()
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(
            username=username,
            password=hash
        )
        db.session.add(user)
    else:
        user.password = hash

    db.session.commit()
    return { 'success': True }

@main.route('/logout', methods = ['GET'])
def logout():
    user = get_user(request.cookies.get('auth'))
    if user is not None:
        user.auth = uuid4().hex
        db.session.commit()
    return redirect('/')

@main.route('/upload', methods = ['POST'])
def upload():
    user = get_user(request.cookies.get('auth'))
    if user is None:
        return { 'success': False, 'message': 'You must be logged in to upload' }

    if 'filecontent' not in request.files or 'filename' not in request.form or 'test' not in request.form:
        return { 'success': False , 'message': 'missing parameters!' }

    test_only = request.form['test'] == 'true'
    filename = request.form['filename'][:32]
    filecontent = request.files['filecontent'].read()[:1024*1024] # 1 MiB
    if len(filename) == 0 or len(filecontent) == 0:
        return { 'success': False , 'message': 'at least one of the parameters was invalid!' }

    if not test_only:
        anims = Animation.query.filter_by(owner=user.username).all()
        if len(anims) >= Config.MAX_ANIM_PER_USER:
            return { 'success': False, 'message': f'Max. number of animations reached ({Config.MAX_ANIM_PER_USER})' }

    animation_id = uuid4().hex
    diskfilename = f'{animation_id}.py'
    diskfilepath = os.path.join(os.getcwd(), Config.FLASK_APP, 'animations', diskfilename)
    try:
        with open(diskfilepath, 'wb') as fd:
            fd.write(filecontent)
    except Exception as e:
        return { 'success': False , 'message': f'Error writing file: {str(e)}' }

    try:
        byte_code = safe_run.load_and_test_animation(diskfilepath)
    except Exception as e:
        os.remove(diskfilepath)
        return { 'success': False, 'message': f'{str(e)}' }

    # Process test request
    if test_only:
        # Delete file
        os.remove(diskfilepath)
        if ctrl.CTRL_IS_TESTING:
            return { 'success': False, 'message': 'test already running' }
        ctrl.ANIMATION_TEST_BYTECODE = byte_code
        ctrl.ANIMATION_TEST_USER = user.username
        return { 'success': True, 'message': 'test submitted' }

    anim = Animation(
        id=animation_id,
        owner=user.username,
        name=filename
    )
    db.session.add(anim)
    db.session.commit()

    return { 'success': True, 'message': 'Upload successful!' }

@main.route('/download/<string:file_id>', methods = ['GET'])
def download(file_id):
    user = get_user(request.cookies.get('auth'))
    if user is None:
        abort(404)
    animation = Animation.query.filter_by(id=file_id).first()
    if animation is None:
        abort(404)
    return send_from_directory(os.path.join(os.getcwd(), Config.FLASK_APP, 'animations'), f'{file_id}.py')

@main.route('/delete/<string:file_id>', methods = ['GET'])
def delete(file_id):
    user = get_user(request.cookies.get('auth'))
    if user is None:
        abort(404)
    animation = Animation.query.filter_by(id=file_id).first()
    if animation is None:
        abort(404)
    try:
        os.remove(os.path.join(os.getcwd(), Config.FLASK_APP, 'animations', f'{file_id}.py'))
        db.session.delete(animation)
        db.session.commit()
    except OSError:
        pass
    return redirect('/')

@main.route('/nowplaying', methods = ['GET'])
def nowplaying():
    return { 'data': f'{get_currently_playing()}' }

@main.route('/logs', methods = ['GET'])
def logs():
    timezone = pytz.timezone('Europe/Bucharest')
    formatted_date = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")

    logs = ctrl.LOG[::-1].copy()
    messages = {}
    for i in range(len(logs)):
        messages[i] = logs[i]
    return render_template('logs.html', current_date=formatted_date, messages=messages)