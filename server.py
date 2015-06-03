"""Audio Project"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session
from flask import url_for, send_from_directory, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from werkzeug import secure_filename

import os
import string
import random

import requests

import twilio.twiml
from twilio.rest import TwilioRestClient

import speech_recognition as sr
import urllib2

from model import User, Upload, Collection, RequestID, CollectionsUsers
from model import CollectionsUploads, connect_to_db, db

import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from StringIO import StringIO

# Your Account Sid and Auth Token from twilio.com/user/account
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token  = os.environ['TWILIO_AUTH_TOKEN']
client = TwilioRestClient(account_sid, auth_token)

# connect to s3 - uses .boto file for aws credentials
conn = S3Connection()

# s3 connection and bucket definition
c = boto.connect_s3()
b = c.get_bucket('radhackbright')

UPLOAD_FOLDER = 'https://s3.amazonaws.com/radhackbright'
ALLOWED_EXTENSIONS = set(['wav'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

app.jinja_env.undefined = StrictUndefined


def request_generator(size=5, chars=string.digits):
	"""Generate numerical string for unique request ID."""

	request_id = ''.join(random.choice(chars) for _ in range(size))
	existing_request = RequestID.query.filter_by(id=request_id).first()

	while existing_request == None: 
		return request_id

	request_id = ''.join(random.choice(chars) for _ in range(size))


def str_generator(size=5, chars=string.ascii_uppercase + string.digits):
	"""Generate string for creating unique filename."""

	rand_str = ''.join(random.choice(chars) for _ in range(size))
	existing_filename = Upload.query.filter_by(path=rand_str).first()

	while existing_filename == None:
		return rand_str

	rand_str = ''.join(random.choice(chars) for _ in range(size))


def is_allowed_file(filename):
	"""Check that file created by audio has allowed extension."""

	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
	"""Serve up files from the /uploads folder."""

	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/')
def index():
	"""Home."""

	if 'email' in session: 
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()
		return redirect('/profile')
	else:
		return render_template('home.html')


@app.route('/profile')
def user_page():
	"""Show more information about the single user logged in."""

	if 'email' in session:
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		user_uploads = user.uploads
		user_collections = user.collections

		# create list of user collectionuploads
		user_cu = []
		for collection in user_collections:
			cu = collection.collectionsuploads
			for i in cu:
				user_cu.append(i.upload_id)

		# initiate list for upload objects unattached to collection
		singleuploads = []
		for i in user_uploads:
			if i.id not in user_cu:
				singleuploads.append(i)

		return render_template("profile.html", user=user,
			singleuploads=singleuploads, upload_folder=UPLOAD_FOLDER)

	else:
		flash('You must be logged in to view files')
		return redirect('/login')


@app.route('/record', methods=['GET', 'POST'])
def record_audio():
	"""Record audio. Capture data and be able to callback."""

	if 'email' in session: 
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		if request.method == 'POST':
			file = request.files['file']
			title = request.form.get('title')
			transcript = request.form.get('transcript')

			if file:
				filename = str_generator(30) + '.wav'
				new_recording = Upload(user_id=user.id, title=title,
					path=filename, transcript=transcript)
				db.session.add(new_recording)
				db.session.commit()

				# save audio file to S3 bucket
				k = b.new_key(filename)
				k.set_contents_from_file(file)

		return render_template('record.html')

	else:
		flash('You must be logged in to save recording')
		return redirect('/login')


@app.route('/generate', methods=['GET', 'POST'])
def generate_request_str():
	"""Generate random, unique string for private user associated URLs."""

	# initialize generated_url
	generated_url = False
	request_number = False

	if 'email' in session: 
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		if request.method == 'POST':
			if 'twilio' in request.form:
				request_str = request_generator()
			
				title = request.form.get('title')
				tel_number = request.form.get('tel')

				new_upload_placeholder = Upload(user_id=user.id, title=title)
				db.session.add(new_upload_placeholder)
				db.session.commit()

				new_upload_id = new_upload_placeholder.id
				new_request = RequestID(id=request_str, user_id=user.id, 
					upload_id=new_upload_id)
				db.session.add(new_request)
				db.session.commit()

				twilio_number = '+14153196892'

				message = client.messages.create(body="""%s is requesting an 
					audio recording. When you are ready, please call %s with
					Twilio and have this request ID ready: %s!""" % 
					(user.first_name, twilio_number, request_str),

				to='+1' + tel_number, # number to send request
				from_="+14153196892") # Twilio number

				request_number = request_str

			else: 
				request_str = request_generator()
				print 'Generated request string', request_str
			
				title = request.form.get('title')

				new_upload_placeholder = Upload(user_id=user.id, title=title)

				db.session.add(new_upload_placeholder)
				db.session.commit()

				new_upload_id = new_upload_placeholder.id
				new_request_url = RequestID(id=request_str, user_id=user.id,
					upload_id=new_upload_id)

				db.session.add(new_request_url)
				db.session.commit()

				generated_url = request_str

	else:
		flash('You must be logged in to generate request URL!')
		return redirect('/login')

	return render_template("generate.html", generated_url=generated_url,
		request_number=request_number)


@app.route("/incoming", methods=['GET', 'POST'])
def incoming_call():
	"""Respond to incoming requests via Twilio call."""
	
	from_number = request.values.get('From', None)
	print 'Number: ', from_number
	call_sid = request.values.get("CallSid", None)

	# check if this is a user number
	from_number = from_number.replace('+1', '')
	print from_number
	user = User.query.filter_by(tel=from_number).first()
	print user

	resp = twilio.twiml.Response()

	if user != None:
		# greet the caller
		resp.say("Hello, %s." % user.first_name)

		resp.say("""Start recording your story after the tone. 
			After you are finished recording, press any key to confirm.""")

		request_str = request_generator()
		new_upload_placeholder = Upload(user_id=user.id)
		db.session.add(new_upload_placeholder)
		db.session.commit()
		print new_upload_placeholder

		new_upload_id = new_upload_placeholder.id
		new_request = RequestID(id=request_str, user_id=user.id, 
								upload_id=new_upload_id, call_sid=call_sid)
		db.session.add(new_request)
		db.session.commit()
		print new_request

		message = client.messages.create(body="""Your story ID is %s.""" % 
		(request_str),

		to='+1' + user.tel, # number to send request
		from_="+14153196892") # Twilio number

		resp.record(action="/handle-user-recording")
		return str(resp)

	else: 
		# greet the caller
		resp.say("Hello.")

		# gather digits
		with resp.gather(numDigits=5, action="/handle-key", method="POST") as g:
			g.say("""Please enter the five digit code included in the text message
				request you received.""")
		return str(resp)


@app.route("/handle-key", methods=['GET', 'POST'])
def handle_key():
	"""Handle key press from a user."""

	digits_pressed = request.values.get('Digits', None)
	requestid = RequestID.query.filter_by(id=digits_pressed).first()

	resp = twilio.twiml.Response()

	if requestid == None:
		resp.say("Sorry. That request ID was not found. Please try again.")
		return str(resp)
		return redirect("/incoming")

	else:
		requested_story = Upload.query.filter_by(id=requestid.upload_id).first()
		user = User.query.filter_by(id=requested_story.user_id).first()

		if requested_story.path:
			resp.say("This request has already been submitted. Goodbye.")
			return str(resp)

		else:
			call_sid = request.values.get("CallSid", None)

			# add call_sid to Requests db
			requestid.call_sid = call_sid
			db.session.commit()
		
			resp = twilio.twiml.Response()
			resp.say("""Thank you! %s is requesting a recording for %s. Start
				recording your story after the tone. After you are finished
				recording, press any key to confirm.""" %
				(user.first_name, requested_story.title))
			resp.record(action="/handle-requested-ecording")
			return str(resp)


@app.route("/handle-user-recording", methods=['GET', 'POST'])
def handle_user_recording():
	"""Play back the user's recording."""

	call_sid = request.values.get("CallSid", None)
	recording_url = request.values.get("RecordingUrl", None)
	recording_uri = requests.get(recording_url)
	recording_sid = request.values.get("RecordingSid", None)

	requestid = RequestID.query.filter_by(call_sid=call_sid).first()
	requested_story = Upload.query.filter_by(id=requestid.upload_id).first()
	user = User.query.filter_by(id=requestid.user_id).first()

	resp = twilio.twiml.Response()
	resp.say("Thanks for your story... take a listen.")
	resp.play(recording_url)

	resp.say("Goodbye.")

	# save file to S3
	k = b.new_key(recording_sid + '.wav')
	k.set_metadata('Content-Type', 'audio/wav')
	k.set_contents_from_string(recording_uri.content)
	k.set_acl('public-read')

	filename = recording_sid + '.wav'
	requested_story.path = filename
	db.session.commit()
	
	# delete from Twilio servers
	client.recordings.delete(recording_sid)

	return str(resp)


@app.route("/handle-requested-recording", methods=['GET', 'POST'])
def handle_requested_recording():
	"""Play back the caller's recording."""

	call_sid = request.values.get("CallSid", None)
	recording_url = request.values.get("RecordingUrl", None)
	recording_uri = requests.get(recording_url)
	recording_sid = request.values.get("RecordingSid", None)

	requestid = RequestID.query.filter_by(call_sid=call_sid).first()
	requested_story = Upload.query.filter_by(id=requestid.upload_id).first()
	user = User.query.filter_by(id=requestid.user_id).first()

	resp = twilio.twiml.Response()
	resp.say("Thanks for your story... take a listen.")
	resp.play(recording_url)

	resp.say("Goodbye.")

	# save file to S3
	k = b.new_key(recording_sid + '.wav')
	k.set_metadata('Content-Type', 'audio/wav')
	k.set_contents_from_string(recording_uri.content)
	k.set_acl('public-read')

	filename = recording_sid + '.wav'
	requested_story.path = filename
	db.session.commit()
	
	# delete from Twilio servers
	client.recordings.delete(recording_sid)

	return str(resp)


@app.route('/listen/<int:id>')
def listen_audio(id):
	"""Show more information about the single user logged in."""

	if 'email' in session: 
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		this_file = Upload.query.filter_by(id=id).first()

		# check if upload belongs to a collection
		cu = this_file.collectionsuploads
		print 'CollectionsUploads: ', cu

		collection = [cu.collection for cu in cu]
		print 'This is the parent collection: ', collection

		collect_users = []
		for c in collection:
			for i in c.collectionsusers:
				print 'what is i', i
				collect_users.append(i.user_id)

		if (this_file.user_id == user.id) or (user.id in collect_users):
			return render_template('listen.html', user=user, upload=this_file,
				upload_folder=UPLOAD_FOLDER)

		else:
			flash('You don\'t have access to view this page')
			return redirect('/')

	else:
		flash('You must be logged in to access this page.')
		return redirect('/')


@app.route('/generate-transcript/<int:id>')
def generate_transcript(id):
	"""Generate transcript if none exists for audio via Twilio calls."""

	this_file = Upload.query.filter_by(id=id).first()
	open_file = urllib2.urlopen(UPLOAD_FOLDER + '/' + this_file.path)
	
	# if this_file.transcript == None:
	# 	r = sr.Recognizer()
	# 	with sr.WavFile(open_file) as source:   
	# 		# extract audio data from the file           
	# 		audio = r.record(source)                        

	# 	try:
	# 		# recognize speech using Google Speech Recognition
	# 		print("Transcription: " + r.recognize(audio))   
	# 		generated_transcript = r.recognize(audio)

	# 		this_file.transcript = generated_transcript
	# 		# db.session.commit()

	# 	except LookupError:     
	# 		# speech is unintelligible                            
	# 		print("Could not understand audio")

	generated_transcript = 'This is a test! <p>Yay, paragraphs!</p>'

	return jsonify(transcript=generated_transcript)    


@app.route('/edit/title/<int:id>', methods=['GET', 'POST'])
def edit_title(id):
	"""Edit an upload title inline."""

	upload_id = id

	if 'email' in session:
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()
		print user

		upload = Upload.query.get(id)
		print '***** upload: ', upload

		name = request.form.get('name')
		print request.form
		print name

		upload.title = name
		db.session.commit()
			
		return redirect('/profile')

	else:
		flash('You must be logged in to view files')
		return redirect('/login')


@app.route('/collection/<int:id>')
def collection_page(id):
	"""Show more information about a collection."""

	if 'email' in session:
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		this_collection = Collection.query.filter_by(id=id).first()

		# create list of uploads attached to current collection
		uploads = [cu.upload for cu in this_collection.collectionsuploads]

		# get list of users with permission for viewing collection
		collectionusers = CollectionsUsers.query.filter_by(
			collection_id=id).all()
		print 'ALLOWED USERS: ', collectionusers

		user_permissions = []
		for u in collectionusers:
			user_permissions.append(u.user_id)

		print 'list of user id: ', user_permissions

		if (this_collection.user_id == user.id) or (
			user.id in user_permissions):
			return render_template('collection.html', user=user,
				collection=this_collection, uploads=uploads)
		
		else:
			flash('You don\'t have access to view this page')
			return redirect('/')

	else:
		flash('You must be logged in to view this page')
		return redirect('/')


@app.route('/add/<int:id>', methods=['GET', 'POST'])
def add_to_collection(id):
	"""Add an existing upload to a collection."""

	upload_id = id

	if 'email' in session:
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		this_collection = request.form['collection']
		existing_collection = Collection.query.filter_by(title=this_collection,
			user_id=user.id).first()

		if existing_collection == None: 
			new_collection = Collection(title=this_collection, user_id=user.id)
			db.session.add(new_collection)
			db.session.commit()
			print 'Added new collection to db: ', new_collection

			add_this_upload = CollectionsUploads(
				collection_id=new_collection.id, upload_id=upload_id)
			db.session.add(add_this_upload)
			db.session.commit()
			print 'Added new upload to collection: ', add_this_upload

			flash('Successfully added to collection')
			return redirect('/profile')

		else: # associate this upload to the already existing collection
			print 'Existing collection id: ', existing_collection.id
			print 'Upload id: ', upload_id
			add_this_upload = CollectionsUploads(
				collection_id=existing_collection.id, upload_id=upload_id)
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

	upload_id = request.form.get('upload_id')
	upload = Upload.query.get(id)

	collection_id = request.form.get('collection_id')
	collection = Collection.query.get(collection_id)

	if 'email' in session: 
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		# check if upload is in current collection
		current_cu = CollectionsUploads.query.filter_by(
			collection_id=collection.id, upload_id=upload.id).first()

		# check if upload is associated with other collection
		other_cu = CollectionsUploads.query.filter_by(
			upload_id=upload.id).first()

		if other_cu == None:
			add_to_collect = CollectionsUploads(collection_id=collection.id,
				upload_id=upload_id)
			db.session.add(add_to_collect)
			db.session.commit()

		elif current_cu:
			print 'Nothing, upload is already part of this collection.'
			flash('')

		else:
			other_cu.collection_id = collection.id
			db.session.commit()
			print 'switched collections'

		return redirect('/profile')

	else:
		flash('You must be logged in to view files')
		return redirect('/login')



@app.route('/share/<int:id>', methods=['GET', 'POST'])
def share_collection(id):
	"""Share a collection with another user by email address."""

	collection_id = id

	if 'email' in session: 
		user_email = session['email']
		user = User.query.filter_by(email=user_email).first()

		other_user_email = request.form['email']
		other = User.query.filter_by(email=other_user_email).first()
		print 'Other user to share with: ', other

		if other == None: # if no user exists
			flash('No user currently exists with this email.')
			return redirect('/profile')

		else:
			shared_with_user = CollectionsUsers(collection_id=collection_id,
				user_id=other.id)
			db.session.add(shared_with_user)
			db.session.commit()
			print 'Added new user to collection: ', shared_with_user

			flash('Shared with %s' % other.email)
			return redirect('/profile')
			

@app.route('/request/<string:id>', methods=['GET', 'POST'])
def requested_audio_page(id):
	"""Show more information about the single user logged in."""

	requested_obj = Request.query.get(id)
	assoc_upload = Upload.query.get(requested_obj.upload_id)

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


@app.route('/success')
def success_message_record():
	"""Flash a success message and redirect to user profile at submit."""

	flash('Recording successfully submitted!')
	return redirect('/profile')


@app.route('/success-collection')
def success_message_upload():
	"""Flash a success message and redirect to user profile at submit."""

	upload_id = request.args.get('UPLOAD_ID')
	upload = Upload.query.get(upload_id)

	collection_id = request.args.get('COLLECTION_ID')
	collection = Collection.query.get(collection_id)

	flash('Upload %s added to collection %s!' % (
		upload.title, collection.title))
	return redirect('/profile')


@app.route('/thanks')
def thanks_message_request():
	"""Flash a success message and redirect to thank you page with info."""

	flash('Recording successfully submitted!')
	return render_template('thanks.html')


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
	entered_tel = request.form['tel']
	entered_pw = request.form['password']
	entered_pw2 = request.form['password2']

	user = User.query.filter_by(email=entered_email).first()

	if request.method == "POST":
		if user == None: 
			if entered_pw != entered_pw2:  
				flash("Your passwords did not match")
				return redirect("/signup")
			
			else:
				# update password into database
				new_user = User(email= entered_email, password = entered_pw,
					first_name=entered_fname, last_name=entered_lname, tel=entered_tel) 
				db.session.add(new_user)
				db.session.commit()

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

	flash("You have successfully logged out.")
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