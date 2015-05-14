"""Audio Project"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, url_for, send_from_directory
from flask_debugtoolbar import DebugToolbarExtension

from werkzeug import secure_filename

import os

from model import User, Upload, Collection, RequestURLs, CollectionsUsers, CollectionsUploads, connect_to_db, db

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
    flash('Welcome!')
    return render_template("homepage.html")


# Start of Recording
def is_allowed_file(filename):
	print 'filename: ', filename
	print '**************'
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/record', methods=['GET', 'POST'])
def record_audio_test():
	"""Record audio. Capture data and be able to callback."""
	print 'GET method on record-test'

	if request.method == 'POST':
		flash('Saved file!')
		print 'is there a file attached? ', request.files
		file = request.files['file']
		print file
		if file and is_allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

			return redirect('/')
	else: 
		return render_template("record.html")



@app.route('/record-loggedin', methods=['GET', 'POST'])
def record_user_audio_test():
	"""Record audio. Capture data and be able to callback."""
	print 'GET method on record-test'
	
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
			desc = request.form.get('desc')
			print file

			if file and is_allowed_file(file.filename):
				filename = secure_filename(file.filename)
				new_recording = Upload(user_id=user.id, title=title, description=desc,
					path=filename)
				print 'Created new recording ', new_recording
				db.session.add(new_recording)
				print 'Adding new recording'
				db.session.commit()
				print 'Committed new recording %s' % filename

				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

	else:
		flash('You must be logged in to save recording')
		return redirect('/login')

	return render_template("record-test.html")





@app.route('/generate')
def generate_urls():
	"""Generate random, unique string for private user associated URLs."""
	pass


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/user/<int:id>')
def user_page(id):
	"""Show more information about the single user logged in."""
	user = User.query.get(id)

	return render_template("user_page.html", user=user)


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