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
	if "email" in session: 
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()
		return redirect('/profile')
	else:
		return render_template('homepage.html')


# Start of Recording
def is_allowed_file(filename):
	print 'filename: ', filename
	print '**************'
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/record', methods=['GET', 'POST'])
def record_audio():
	"""Record audio. Capture data and be able to callback."""

	if "email" in session: # if logged in
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

		return render_template('record.html')

	else:
		flash('You must be logged in to save recording')
		return redirect('/login')


@app.route('/success')
def success_message_record():
	"""Flash a success message and redirect to user profile at submit."""
	flash('Recording successfully submitted!')
	return redirect('/profile')


@app.route('/success-collection')
def success_message_upload():
	"""Flash a success message and redirect to user profile at submit."""
	flash('Upload added to collection!')
	return redirect('/profile')


@app.route('/thanks')
def thanks_message_request():
	"""Flash a success message and redirect to thank you page with info."""
	flash('Recording successfully submitted!')
	return render_template('thanks.html')


def id_generator(size=20, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))


@app.route('/generate', methods=['GET', 'POST'])
def generate_request_str():
	"""Generate random, unique string for private user associated URLs."""

	generated_url = False

	if "email" in session: # if logged in
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

	if "email" in session: # if logged in
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		user_uploads = user.uploads
		print "user uploads: ", user_uploads

		user_collections = user.collections
		print "user collections: ", user_collections

		user_cu = []

		for collection in user_collections:
			cu = collection.collectionsuploads
			for i in cu:
				user_cu.append(i.upload_id)

		singleuploads = []

		for i in user_uploads:
			if i.id not in user_cu:
				singleuploads.append(i)

		print '**** Unattached uploads: ', singleuploads

		# print "user collectionsuploads: ", user_cu


		return render_template("profile2.html", user=user, singleuploads=singleuploads)

	else:
		flash('You must be logged in to view files')
		return redirect('/login')


@app.route('/listen/<int:id>')
def listen_audio(id):
	"""Show more information about the single user logged in."""

	if "email" in session: # if logged in
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()
		print "User ID of this user: ", user.id

		this_file = Upload.query.filter_by(id=id).first()
		print "User ID of this file: ", this_file.id

		# check if upload belongs to a collection,
		# to check if other users have permission for collection
		# other users inherit the permission for individual audio file
		parent_collections = this_file.collectionsuploads
		print "*******This upload belongs to: ", parent_collections

		# from collections uploads, get collection id
		# from collection id, find collectionsusers
		# from collectionsusers find all users
		# check if logged in user id is in this list for access
		
		if this_file.user_id == user.id:
			return render_template('listen.html', user=user, upload=this_file)

		else:
			flash('You don\'t have access to view this page')
			return redirect('/')


@app.route('/collection/<int:id>')
def collection_page(id):
	"""Show more information about a collection."""

	if "email" in session: # if logged in
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()
		print "User ID of this user: ", user.id

		this_collection = Collection.query.filter_by(id=id).first()
		print "This collection: ", this_collection

		uploads = [cu.upload for cu in this_collection.collectionsuploads]
		print "This collection's uploads: ", uploads

		print "CollectionsUsers before query: ", this_collection.collectionsusers

		collectionusers = CollectionsUsers.query.filter_by(collection_id=id).all()
		print "This collection to user relationship: ", collectionusers

		return render_template('collection.html', user=user, collection=this_collection, uploads=uploads)

	else:
		flash('You don\'t have access to view this page')
		return redirect('/')


@app.route('/add/<int:id>', methods=['GET', 'POST'])
def add_to_collection(id):
	"""Add an existing upload to a collection."""
	print 'ADD TO COLLECTION *************'
	upload_id = id
	if "email" in session: # if logged in
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		this_collection = request.form['collection']
		existing_collection = Collection.query.filter_by(title=this_collection, user_id=user.id).first()

		if existing_collection == None: # if no collection exists of the same name from this user, create one
			new_collection = Collection(title=this_collection, user_id=user.id)
			db.session.add(new_collection)
			db.session.commit()
			print 'Added new collection to db: ', new_collection

			add_this_upload = CollectionsUploads(collection_id=new_collection.id, upload_id=upload_id)
			db.session.add(add_this_upload)
			db.session.commit()
			print 'Added new upload to collection: ', add_this_upload

			flash('Successfully added to collection')
			return redirect('/profile')

		else: # associate this upload to the already existing collection
			print 'Existing collection id: ', existing_collection.id
			print 'Upload id: ', upload_id
			add_this_upload = CollectionsUploads(collection_id=existing_collection.id, upload_id=upload_id)
			db.session.add(add_this_upload)
			db.session.commit()
			print 'Add this upload to existing collection: ', add_this_upload
			
			flash('Successfully added to collection')

			return redirect('/profile')

	else:
		flash('You must be logged in to view files')
		return redirect('/login')


@app.route('/add-to-collection/<int:id>', methods=['GET', 'POST'])
def add_upload_to_collection(id):
	"""Add an existing upload to a collection."""
	print 'ADD TO COLLECTION *************'
	upload_id = request.form.get('upload_id')
	upload = Upload.query.get(id)
	print 'Upload id: ', upload_id

	collection_id = request.form.get('collection_id')
	collection = Collection.query.get(collection_id)
	print 'Collection id: ', collection_id

	# flash('Successfully added %s to the %s collection' % (upload.title, collection.title))

	return redirect('/profile')



	# if "email" in session: # if logged in
	# 	user_email = session['email']
	# 	user = User.query.filter_by(email=user_email).first()

	# 	this_collection = request.form['collection']
	# 	existing_collection = Collection.query.filter_by(title=this_collection, user_id=user.id).first()

	# 	if existing_collection == None: # if no collection exists of the same name from this user, not possible

	# 		flash('This is not possible')
	# 		return redirect('/profile')

	# 	else: # associate this upload to the already existing collection
	# 		print 'Existing collection id: ', existing_collection.id
	# 		print 'Upload id: ', upload_id
	# 		add_this_upload = CollectionsUploads(collection_id=existing_collection.id, upload_id=upload_id)
	# 		# db.session.add(add_this_upload)
	# 		# db.session.commit()
	# 		print 'Add this upload to existing collection: ', add_this_upload
			
	# 		flash('Successfully added to collection')

	# 		return redirect('/profile')

	# else:
	# 	flash('You must be logged in to view files')
	# 	return redirect('/login')



@app.route('/share/<int:id>', methods=['GET', 'POST'])
def share_collection(id):
	"""Share a collection with another user by email address."""
	print 'SHARING COLLECTION *************'

	collection_id = id

	if "email" in session: # if logged in
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		other_user_email = request.form['email']
		other = User.query.filter_by(email=other_user_email).first()
		print 'Other user to share with: ', other

		if other == None: # if no user exists
			flash('No user currently exists with this email.')
			return redirect('/profile')

		else:
			shared_with_user = CollectionsUsers(collection_id=collection_id, user_id=other.id)
			db.session.add(shared_with_user)
			db.session.commit()
			print 'Added new user to collection: ', shared_with_user

			flash('Shared with %s' % other.email)
			return redirect('/profile')
			

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
	
	if user != None:
		if entered_pw == user.password:
			session['email'] = request.form['email']
			print 'Session: ', session
			flash('You successfully logged in as %s!' % session['email'])
			return redirect("/profile")
		else:
			flash("That is not the correct password!")
			return redirect('/login')
	else:
		flash("No existing account for %s" % entered_email)
		return redirect('/signup')



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