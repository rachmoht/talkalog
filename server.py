"""Audio Project"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, url_for, send_from_directory
from flask_debugtoolbar import DebugToolbarExtension

from werkzeug import secure_filename

import os
import string
import random

from model import User, Upload, Collection, RequestURL, CollectionsUsers, CollectionsUploads, connect_to_db, db

# Required for saving our wav files to our server @ uploads/
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set(['wav'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined



@app.route('/')
def index():
    """Home."""
    return render_template("homepage.html")


# Start of Recording
def is_allowed_file(filename):
	print 'filename: ', filename
	print '**************'
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/record', methods=['GET', 'POST'])
def record_audio():
	"""Record audio. Capture data and be able to callback."""

	if "email" in session: #if logged in
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()
		print 'User: ', user

		if request.method == 'POST':
			flash('Saved file!')
			print 'is there a file attached? ', request.files # gets the ImmutableMultiDict for files
			print 'request form: ', request.form # gets the ImmutableMultiDict for info
			print 'more things, like the title: ', request.form.get('title')
			file = request.files['file']
			title = request.form.get('title')
			transcript = request.form.get('transcript')
			print file

			if file and is_allowed_file(file.filename):
				filename = secure_filename(file.filename)
				new_recording = Upload(user_id=user.id, title=title, path=filename, transcript=transcript)
				print 'Created new recording ', new_recording
				db.session.add(new_recording)
				print 'Adding new recording'
				db.session.commit()
				print 'Committed new recording %s' % filename

				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

				flash('Memo successfully recorded!')
				return redirect('/profile')

		return render_template("record.html")

	else:
		flash('You must be logged in to save recording')
		return redirect('/login')


def id_generator(size=20, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))


@app.route('/generate', methods=['GET', 'POST'])
def generate_request_str():
	"""Generate random, unique string for private user associated URLs."""

	generated_url = False

	if "email" in session: #if logged in
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		if request.method == 'POST':
			request_str = id_generator()
			print 'Generated request string', request_str
		
			title = request.form.get('title')
			print 'This is the title: ', title

			new_upload_placeholder = Upload(user_id=user.id, title=title)

			db.session.add(new_upload_placeholder)
			db.session.commit()

			print 'New Upload ID: ', new_upload_placeholder.id
			new_upload_id = new_upload_placeholder.id
			print 'Generated new upload id: ', new_upload_id
			print 'Created new upload placeholder ', new_upload_placeholder

			print 'Adding new new_upload_placeholder'

			new_request_url = RequestURL(id=request_str, user_id=user.id, upload_id=new_upload_id)
			print 'Created new RequestURL: ', new_request_url

			db.session.add(new_request_url)
			db.session.commit()

			generated_url = request_str

	else:
		flash('You must be logged in to generate request URL!')
		return redirect('/login')

	return render_template("generate.html", generated_url=generated_url)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
	"""This route is required to serve up files from the uploads folder."""
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/profile')
def user_page():
	"""Show more information about the single user logged in."""

	if "email" in session: #if logged in
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		return render_template("user_page.html", user=user)

	else:
		flash('You must be logged in to view files')
		return redirect('/login')


@app.route('/request/<string:id>', methods=['GET', 'POST'])
def requested_audio_page(id):
	"""Show more information about the single user logged in."""
	requested_obj = RequestURL.query.get(id)
	assoc_upload = Upload.query.get(requested_obj.upload_id)
	print assoc_upload

	if request.method == 'POST':
		file = request.files['file']
		print 'FILE: ', file

		title = request.form.get('title')
		print 'TITLE: ', title

		transcript = request.form.get('transcript')
		print 'TRANSCRIPT: ', transcript

		if file and is_allowed_file(file.filename):
			filename = secure_filename(file.filename)
			assoc_upload.title = title
			assoc_upload.path = filename
			assoc_upload.transcript = transcript

			print 'NEW assoc upload: ', assoc_upload

			db.session.commit()
			print 'Committed new recording %s' % filename

			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

	return render_template("request_page.html", requested_obj=requested_obj)



# User Login and Register 
@app.route('/login')
def login_user():
	"""Login page for user."""

	return render_template("login.html")


@app.route('/login-process', methods=['POST'])
def login_process():
	"""Process login for user."""

	entered_email = request.form['email']
	entered_pw = request.form['password']

	user = User.query.filter_by(email=entered_email).first()

	if entered_pw == user.password:
		session['email'] = request.form['email']
		print 'Session: ', session
		flash('You successfully logged in as %s!' % session['email'])
		return redirect("/user/%s" % user.id)
	else:
		flash("That is not the correct password!")
		return redirect('/login')


@app.route('/signup')
def signup_user():
	"""Sign up page for new users."""

	return render_template("signup.html")


@app.route('/signup-process', methods=['POST'])
def signup_process():
	"""Process sign up and login for user."""

	entered_fname = request.form['first_name']
	entered_lname = request.form['last_name']
	entered_email = request.form['email']
	entered_pw = request.form['password']
	entered_pw2 = request.form['password2']

	user = User.query.filter_by(email=entered_email).first()

	if request.method == "POST":
		if user == None: 
			print user 
			if entered_pw != entered_pw2:  
				flash("Your passwords did not match")
				return redirect("/signup")
			else:
				#update password into database
				new_user = User(email= entered_email, password = entered_pw, first_name=entered_fname, last_name=entered_lname) 
				db.session.add(new_user)
				db.session.commit()
				print 'creating new user in Database.'
				print new_user, new_user.id
				session['email'] = entered_email
				flash("You are signed up %s!" % entered_email) 
				return redirect("/")
		else: 
			flash("You have already signed up with that email")
			return redirect('/login')


@app.route("/logout")
def process_logout():
    """Route to process logout for users."""

    session.pop('email')
    flash('You successfully logged out!')
    print session
    return redirect("/")


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()