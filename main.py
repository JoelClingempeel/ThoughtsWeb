import json
import os
import sys

from flask import render_template, session, request, redirect, url_for, Flask
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy


app = Flask('__name__')

if len(sys.argv) > 1 and sys.argv[1] == '--test':
    app.config['SECRET_KEY'] = 'blairehasmyheart'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/thoughtsweb'
else:
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
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
    private = db.Column(db.Boolean)


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


class ProfileDescription(db.Model):
    __tablename__ = 'profile_descriptions'
    username = db.Column(db.String(64), primary_key=True)
    description = db.Column(db.String(3000))


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user1 = db.Column(db.String(64))
    user2 = db.Column(db.String(64))
    text = db.Column(db.String(1000))


class LoginForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    password = PasswordField('Enter the password.')
    submit = SubmitField('submit')


class SignupForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    password1 = PasswordField('Enter the password.')
    password2 = PasswordField('Verify the password.')
    submit = SubmitField('submit')


class EditNoteForm(FlaskForm):
    text = TextAreaField('')
    submit = SubmitField('submit')


class EditProfile(FlaskForm):
    description = TextAreaField('Please enter your profile description here.', validators=[DataRequired()])
    submit = SubmitField('submit')


class SendMessage(FlaskForm):
    message = TextAreaField('Please enter your message here.', validators=[DataRequired()])
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
        if User.query.filter_by(username=form.name.data).first():
            return redirect('error/username_taken')
        elif form.password1.data != form.password2.data:
            return redirect('error/password_mismatch')
        else:
            name = form.name.data
            password = form.password1.data
            new_user = User(username=name, password=password)
            db.session.add(new_user)
            new_profile_description = ProfileDescription(username=name,
                                                         description='This user does not yet have a description.')
            db.session.add(new_profile_description)
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
                      'password_mismatch': 'The passwords you entered do not match.'}
    error = error_messages[type]
    return render_template('error.html', error=error)


@app.route('/profile/<user>')
def profile(user):
    # TODO error handling
    user_description = ProfileDescription.query.filter_by(username=user).first().description
    return render_template('profile.html', user=user, description=user_description)


@app.route('/searchusers')
def searchusers():
    query = request.args.get('user_query')
    raw_users = User.query.filter(User.username.contains(query)).all()
    users = [user.username for user in raw_users]
    return render_template('searchusers.html', users=users)


@app.route('/editprofile', methods=['GET', 'POST'])
def editprofile():
    current_description = ProfileDescription.query.filter_by(username=session['name']).first()
    profile_form = EditProfile()
    if request.method == 'POST':
        current_description.description = profile_form.description.data
        db.session.commit()
    return render_template('editprofile.html', description=current_description.description, form=profile_form)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/messages')
def messages():
    if not session.get('name'):  # Add error message on redirect.
        return redirect(url_for('login'))
    sent_messages = Message.query.filter_by(user1=session.get('name')).all()
    received_messages = Message.query.filter_by(user2=session.get('name')).all()
    user_list = [msg.user2 for msg in sent_messages] + [msg.user1 for msg in received_messages]
    return render_template('messages.html', user_list=list(set(user_list)))


@app.route('/message/<user>', methods=['GET', 'POST'])
def message(user):
    if not session.get('name'):  # Add error message on redirect.
        return redirect(url_for('login'))
    # TODO need to validate other user exists and is not you
    # Get existing messages
    display_list = []
    existing_sent_messages = Message.query.filter_by(user1=session.get('name'), user2=user).all()
    for msg in existing_sent_messages:
        display_list.append([msg.id, msg.user1, msg.text])
    existing_received_messages = Message.query.filter_by(user2=session.get('name'), user1=user).all()
    for msg in existing_received_messages:
        display_list.append([msg.id, msg.user1, msg.text])
    display_list.sort()
    display_list = [msg[1:] for msg in display_list]
    # Handle new messages
    message_form = SendMessage()
    if request.method == 'POST':
        new_message = Message(user1=session.get('name'), user2=user, text=message_form.message.data)
        db.session.add(new_message)
        db.session.commit()
        display_list.append([session.get('name'), message_form.message.data])
    return render_template('message.html', display_list=display_list, form=message_form)


@app.route('/graph')
def graph():
    return render_template("graph.html")


@app.route('/trending')
def trending():
    # Get node counts.
    nodes = Node.query.filter_by(private=False).all()
    counts = {}
    for node in nodes:
        counts[node.label] = counts.get(node.label, 0) + 1

    # Get note counts.
    note_edges = Edge.query.filter_by(type='note')
    note_counts = {}
    for edge in note_edges:
        note_counts[edge.sink] = note_counts.get(edge.sink, 0) + \
                                 Node.query.filter_by(label=edge.sink, private=False).count()

    data = []
    for node, count in counts.items():
        data.append([count, note_counts.get(node, 0), node])
    data.sort(reverse=True)
    return render_template("trending.html", data=data)


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
                type=request.get_json()['type'],
                private=True)
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


@app.route('/get_node_data', methods=['POST'])
def get_node_data():  # TODO Add better handling of global nodes.
    # Get global-ness and privacy.
    node_ob = Node.query.filter_by(label=request.get_json()['node'],
                                   username=session['name']).first()
    if node_ob:
        is_global = False
        private = node_ob.private
    else:
        is_global = True
        private = False

    # Get Note count.
    num_notes = Edge.query.filter_by(sink=request.get_json()['node'],
                                     username=session['name'],
                                     type='note').count()

    # Get Global Note count.
    num_global_notes = 0
    global_note_edges = Edge.query.filter_by(sink=request.get_json()['node'],
                                             type='note').all()
    for edge in global_note_edges:
        note_nodes = Node.query.filter_by(label=edge.source, private=False).all()
        for node in note_nodes:
            if node.username != session['name']:
                num_global_notes += 1

    # Get note (if applicable).
    note = Note.query.filter_by(node=request.get_json()['node']).first()
    if note:
        # TODO Remove using explicit link.
        if note.username == session['name']:
            note_data = f'<a href="edit_note/{note.node}"> Edit </a> <br />' + note.text
        else:
            note_data = note.text
    else:
        note_data = ''

    # Get other users (for global nodes).
    if is_global:
        other_user_nodes = Node.query.filter_by(label=request.get_json()['node'],
                                                private=False).all()
        other_users = [node.username for node in other_user_nodes
                       if node.username != session['name']]
    else:
        other_users = []

    return json.dumps({'is_global': str(is_global),
                       'private': str(private),
                       'num_notes': str(num_notes),
                       'num_global_notes': str(num_global_notes),
                       'other_users': other_users,
                       'note': note_data})


@app.route('/graph_snapshot', methods=['POST'])
def graph_snapshot():
    nodes = Node.query.filter_by(username=session['name'], type='entity').all()
    edges = Edge.query.filter_by(username=session['name']).all()
    return json.dumps({'nodes': [[node.label, node.type] for node in nodes],
                       'edges': [[edge.source, edge.sink, edge.label]
                                 for edge in edges if edge.type != 'note']})


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


@app.route('/get_neighbors', methods=['POST'])
def get_neighbors():
    in_edges = Edge.query.filter_by(sink=request.get_json()['node'],
                                    username=session['name']).all()
    out_edges = Edge.query.filter_by(source=request.get_json()['node'],
                                     username=session['name']).all()
    node_labels = [edge.source for edge in in_edges] + [edge.sink for edge in out_edges]

    nodes = []
    for label in node_labels:
        node = Node.query.filter_by(label=label,
                                    username=session['name'],
                                    type='entity').first()
        nodes.append([node.label, node.type])
    node_labels.append(request.get_json()['node'])  # Needed for finding edge relations

    edges = []
    all_edges = Edge.query.filter_by(username=session['name']).all()
    for edge in all_edges:
        if edge.source in node_labels and edge.sink in node_labels and edge.type != 'note':
            edges.append([edge.source, edge.sink, edge.label])

    return json.dumps({'nodes': nodes, 'edges': edges})


@app.route('/get_global_neighbors', methods=['POST'])
def get_global_neighbors():
    in_edges = Edge.query.filter_by(sink=request.get_json()['node']).all()
    out_edges = Edge.query.filter_by(source=request.get_json()['node']).all()
    node_labels = [edge.source for edge in in_edges if edge.username != session['name']] + \
                  [edge.sink for edge in out_edges if edge.username != session['name']]

    nodes = []
    for label in node_labels:
        node = Node.query.filter_by(label=label,
                                    private=False,
                                    type='entity').first()
        if node and node.username != session['name']:
            nodes.append([node.label, 'global_entity'])
    node_labels.append(request.get_json()['node'])  # Needed for finding edge relations

    edges = []
    all_edges = Edge.query.all()
    for edge in all_edges:
        if (edge.source in node_labels and edge.sink in node_labels
                and edge.type != 'note' and edge.username != session['name']):
            edges.append([edge.source, edge.sink, edge.label])

    return json.dumps({'nodes': nodes, 'edges': edges})


@app.route('/get_notes', methods=['POST'])
def get_notes():
    note_edges = Edge.query.filter_by(sink=request.get_json()['node'],
                                      username=session['name'],
                                      type='note').all()
    nodes = []
    for edge in note_edges:
        node = Node.query.filter_by(label=edge.source,
                                    username=session['name']).first()
        nodes.append([node.label, node.type])
    node_labels = [node[0] for node in nodes]

    edges = []
    all_edges = Edge.query.filter_by(username=session['name']).all()
    for edge in all_edges:
        if edge.source in node_labels and edge.sink == request.get_json()['node']:
            edges.append([edge.source, edge.sink, edge.label])

    return json.dumps({'nodes': nodes, 'edges': edges})


@app.route('/get_global_notes', methods=['POST'])
def get_global_notes():
    note_edges = Edge.query.filter_by(sink=request.get_json()['node'],
                                      type='note').all()
    nodes = []
    for edge in note_edges:
        node = Node.query.filter_by(label=edge.source,
                                    private=False).first()
        if node:
            nodes.append([node.label, 'global_note'])
    node_labels = [node[0] for node in nodes]

    edges = []
    all_edges = Edge.query.filter_by().all()
    for edge in all_edges:
        if edge.source in node_labels and edge.sink == request.get_json()['node']:
            edges.append([edge.source, edge.sink, edge.label])

    return json.dumps({'nodes': nodes, 'edges': edges})


@app.route('/node_search', methods=['POST'])
def node_search():
    query = request.get_json()['query']
    nodes = Node.query.filter_by(type='entity',
                                 private=False).all()
    results = [[node.label, 'global_entity'] for node in nodes
               if query in node.label]
    return json.dumps({'nodes': results, 'edges': []})


@app.route('/toggle_privacy', methods=['POST'])
def toggle_privacy():
    node = Node.query.filter_by(label=request.get_json()['node'],
                                username=session['name']).first()
    node.private = not node.private
    db.session.commit()
    return json.dumps({})


if __name__ == '__main__':
    app.run(debug=True)
