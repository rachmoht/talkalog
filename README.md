# Talkalog

Talkalog is the easiest way to request, create, store, and manage audio recordings. Send a request to your grandmother to record her coveted family recipes, generate and edit the transcripts, and create a recipe book instantly.

#### Technology Stack

JavaScript, jQuery, HTML, Sass, Bootstrap, Python, Flask, Jinja, SQLAlchemy, SQLite, Amazon S3, <a href="https://jqueryui.com/draggable/" target="_blank">jQuery UI Draggable and Droppable</a>, <a href="http://getbootstrap.com/javascript/#collapse" target="_blank">Bootstrap Collapse.js</a>, and <a href="http://vitalets.github.io/x-editable/" target="_blank">X-editable</a>

#### APIs

<a href="http://twilio.com/" target="_blank">Twilio SMS and Voice</a>, <a href="https://developers.google.com/web/updates/2013/01/Voice-Driven-Web-Apps-Introduction-to-the-Web-Speech-API?hl=en" target="_blank">Web Speech</a> / <a href="https://pypi.python.org/pypi/SpeechRecognition/" target="_blank">Speech Recognition</a>, <a href="https://github.com/mattdiamond/Recorderjs" target="_blank">Recorder.js</a>, <a href="https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API" target="_blank">HTML5 Web Audio</a>, <a href="http://ckeditor.com/" target="_blank">CKEditor</a>

#### Discussion on Technologies

As a former front-end developer and designer, one of my main goals was to make Talkalog as intuitive as possible for all users: the requesters and the storytellers. Talkalog was inspired by my desire to capture my family's oral history, mainly stories from my grandparents. This is the main reason I wanted the interface and interactions to be clean, easy, and straightforward for all users no matter what age, level of tech savvy, or web accessibility.

On the web interface, Talkalog uses the **Recorder.js** and **HTML5 Web Audio APIs** to capture audio recordings. These audio APIs are integrated with **Google's Speech Recognition API** to generate the text transcript alongside the recording.

Talkalog also provides a phone interface option, where **Twilio** is used to allow storytellers to call in at their leisure. 

After phone recordings are created, the WAVE file can be served up from **Amazon S3**, converted into FLAC format, and then processed through Speech Recognition at the user's discretion. This was originally implemented after running into Twilio's two minute transcript limit.

## Overview

In most scenarios, Talkalog has two user roles: the _requester_ and _storyteller_.

##### User Story Example:
1. Requester logs in and makes a request
2. Request is sent to storyteller via URL or SMS
3. Storyteller arrives at Request URL or call
4. Storyteller is prompted to begin recording 
5. Recording is saved and routed into requester's Talkalog account
6. Requester can now control permissions and sharing, transcript formatting, and more

___

### Requesting Audio

Requests can be generated and sent to the storyteller by **two options**. 

<img src="/static/img/readme/story_request.png" alt="Generate Story Request">

###### 1. Requesting Audio: Web Interface
A request web page: e.g. _domain.com/request/12345_ 

<img src="/static/img/readme/request_web.png" alt="Story Request | Web">

The storyteller, without needing to register or sign into an account, is routed to this private request page to gather the recording, transcript, and other information:

<img src="/static/img/readme/request_web_flow.png" alt="Story Request | Web Flow">

###### 2. Requesting Audio: Phone Interface
A request SMS and call

> Rachelle is requesting an audio recording for "Grandma's Secret Recipe". When you are ready, please call +18005555555 and have this request ID ready: **12345**

The storyteller will call in, enter the request ID digits, and start speaking when prompted:

<img src="/static/img/readme/request_phone_flow.png" alt="Story Request | Phone Flow">

###### A Note on How Audio is Processed

As seen in the flow charts above, both requests handle the audio upload in similar ways, utilizing the unique Request ID and the Twilio Call SID to associate the newly created file and file path with the upload record created at the time of the request. With the help of Boto, Talkalog processes the audio blob, sends, and stores the audio file in an **Amazon S3** bucket.

___

### User Profile

<img src="/static/img/readme/user_profile.png" alt="User Profile">

The user profile interface showcases a list of the user's collections and associated uploads. Users are able to drag and drop, collapse, and edit titles inline thanks to <a href="https://jqueryui.com/draggable/" target="_blank">jQuery UI Draggable and Droppable</a>, <a href="http://getbootstrap.com/javascript/#collapse" target="_blank">Bootstrap Collapse.js</a>, and <a href="http://vitalets.github.io/x-editable/" target="_blank">X-editable</a>.

___

### Listening to Audio and Reading/Editing Transcripts

Text transcripts are generated either live during the recording if via web URL or at the requestor's discretion if the recording was captured over a phone call. All transcripts can be edited after the recording for accuracy and nice formatting using the rich text editor.

<img src="/static/img/readme/listen.png" alt="Listen and Read">

<img src="/static/img/readme/edit_transcript.png" alt="Edit Transcript">

___

### Data Model

<img src="/static/img/readme/data_model.png" alt="Talkalog Data Model" style="max-width: 100%;">
