import json
from flask import render_template, session, request, redirect, url_for, Flask
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy

app = Flask('__name__')
app.config['SECRET_KEY'] = 'blairehasmyheart'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/thoughtsweb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(64), primary_key=True)
    password = db.Column(db.String(64))


class Node(db.Model):
    __tablename__ = 'nodes'
    label = db.Column(db.String(64))
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    type = db.Column(db.String(64))


class Edge(db.Model):
    __tablename__ = 'edges'
    source = db.Column(db.String(64))
    sink = db.Column(db.String(64))
    label = db.Column(db.String(64))
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    type = db.Column(db.String(64))


class Note(db.Model):
    __tablename__ = 'notes'
    node = db.Column(db.String(64))
    text = db.Column(db.String(5000))  # TODO enforce this char limit (or raise it?)
    username = db.Column(db.String(64))
    id = db.Column(db.Integer, primary_key=True)


class LoginForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    password = PasswordField('Enter the password.')
    submit = SubmitField('submit')


class SignupForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    password1 = PasswordField('Enter the password.')
    password2 = PasswordField('Verify the password.')
    password_beta = PasswordField('Enter your beta testing password.')
    submit = SubmitField('submit')


class EditNoteForm(FlaskForm):
    text = TextAreaField('')
    submit = SubmitField('submit')


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        candidate_user = User.query.filter_by(username=form.name.data).first()
        if not candidate_user:
            return redirect('error/invalid_username')
        elif form.password.data != candidate_user.password:
            return redirect('error/invalid_password')
        else:
            session['name'] = form.name.data
            return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.name.data).first():  # TODO Check if username is taken.
            return redirect('error/username_taken')
        elif form.password1.data != form.password2.data:
            return redirect('error/password_mismatch')
        elif form.password_beta.data != 'dinoeats314':
            return redirect('error/invalid_beta_password')
        else:
            name = form.name.data
            password = form.password1.data
            new_user = User(username=name, password=password)
            db.session.add(new_user)
            db.session.commit()
            session['name'] = form.name.data
            return redirect(url_for('index'))
    return render_template('signup.html', form=form)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/error/<type>')
def show_error(type):
    error_messages = {'invalid_username': 'The username you entered does not exist',
                      'invalid_password': 'Invalid password!',
                      'username_taken': 'The username you chose is already taken.',
                      'password_mismatch': 'The passwords you entered do not match.',
                      'invalid_beta_password': 'The beta testing password you entered is incorrect.'
                      }
    error = error_messages[type]
    return render_template('error.html', error=error)


@app.route('/graph')
def graph():
    return render_template("graph.html")


@app.route('/edit_note/<node>', methods=['GET', 'POST'])
def edit_note(node):
    current_text = Note.query.filter_by(node=node, username=session['name']).first()
    edit_note_form = EditNoteForm()
    if request.method == 'POST':
        current_text.text = edit_note_form.text.data
        db.session.commit()
    edit_note_form.text.data = current_text.text
    return render_template('edit_note.html', form=edit_note_form)


@app.route('/add_node', methods=['POST'])
def add_node():
    node = Node(label=request.get_json()['label'],
                username=session['name'],
                type=request.get_json()['type'])
    db.session.add(node)
    if request.get_json()['type'] == 'note':
        note = Note(node=request.get_json()['label'],
                    text='To be written...',
                    username=session['name'])
        db.session.add(note)
    db.session.commit()
    return ''


@app.route('/remove_node', methods=['POST'])
def remove_node():
    node = Node.query.filter_by(label=request.get_json()['label'],
                                username=session['name']).first()
    if node.type == 'note':
        Note.query.filter_by(node=request.get_json()['label'],
                             username=session['name']).delete()
    db.session.delete(node)
    # Remove all edges having this node as a source or sink.
    Edge.query.filter_by(source=request.get_json()['label'],
                         username=session['name']).delete()
    Edge.query.filter_by(sink=request.get_json()['label'],
                         username=session['name']).delete()
    db.session.commit()
    return ''


@app.route('/add_edge', methods=['POST'])
def add_edge():
    edge = Edge(source=request.get_json()['source'],
                sink=request.get_json()['sink'],
                label=request.get_json()['label'],
                username=session['name'],
                type=request.get_json()['type'])
    db.session.add(edge)
    db.session.commit()
    return ''


@app.route('/remove_edge', methods=['POST'])
def remove_edge():
    edge = Edge.query.filter_by(source=request.get_json()['source'],
                                sink=request.get_json()['sink'],
                                username=session['name']).first()
    db.session.delete(edge)
    db.session.commit()
    return ''


@app.route('/get_note', methods=['POST'])
def get_note():
    note = Note.query.filter_by(node=request.get_json()['node'],
                                username=session['name']).first()
    if note:
        # TODO Remove using explicit link.
        prefix = f'<a href="http://127.0.0.1:5000/edit_note/{note.node}"> Edit </a> <br />'
        return json.dumps({'note': prefix + note.text})
    else:
        return json.dumps({'note': ''})


@app.route('/graph_snapshot', methods=['POST'])
def graph_snapshot():
    nodes = Node.query.filter_by(username=session['name']).all()
    edges = Edge.query.filter_by(username=session['name']).all()
    return json.dumps({'nodes': [[node.label, node.type] for node in nodes],
                       'edges': [[edge.source, edge.sink, edge.label] for edge in edges]})


@app.route('/get_children', methods=['POST'])
def get_children():
    children = Edge.query.filter_by(sink=request.get_json()['root'],
                                    username=session['name'],
                                    type='hierarchical').all()
    nodes = []
    for child in children:
        node = Node.query.filter_by(label=child.source,
                                    username=session['name']).first()
        nodes.append([node.label, node.type])
    node_labels = [node[0] for node in nodes]

    edges = []
    all_edges = Edge.query.filter_by(username=session['name']).all()
    for edge in all_edges:
        if edge.source in node_labels and edge.sink in node_labels:
            edges.append([edge.source, edge.sink, edge.label])

    return json.dumps({'nodes': nodes, 'edges': edges})


if __name__ == '__main__':
    app.run(debug=True)
