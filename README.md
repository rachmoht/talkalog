# Talkalog

Talkalog is the easiest way to create, request, and store audio recordings. Send a request to your grandmother to record her coveted secret family recipes, generate and edit the transcripts, and have a readymade recipe book instantly.

#### Technology Stack

JavaScript, jQuery, HTML, Sass, Bootstrap, Python, Flask, Jinja, SQLAlchemy, SQLite, Amazon S3

#### APIs

<a href="http://twilio.com/" target="_blank">Twilio SMS and Voice</a>, <a href="https://developers.google.com/web/updates/2013/01/Voice-Driven-Web-Apps-Introduction-to-the-Web-Speech-API?hl=en" target="_blank">Web Speech</a> / <a href="https://pypi.python.org/pypi/SpeechRecognition/" target="_blank">Speech Recognition</a>, <a href="https://github.com/mattdiamond/Recorderjs" target="_blank">Recorder.js</a>, <a href="https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API" target="_blank">HTML5 Web Audio</a>

## Overview

In most scenarios, Talkalog has two user roles: the _requestor_ and _storyteller_.

##### User Story Example:
1. Requestor logs in and makes a request
2. Request is sent to storyteller via URL or SMS
3. Storyteller arrives at Request URL or call
4. Storyteller is prompted to begin recording 
5. Recording is saved and routed into requestor's Talkalog account
6. Requestor can now control permissions and sharing, transcript formatting, and more

___

### Requests

Requests can be generated and sent to the storyteller by two options. At time of generation, a new record is created as a placeholder in the Uploads table.

<img src="/static/img/etc/story_request.png" alt="Generate Story Request">

1. A request web page: e.g. _domain.com/request/12345_ 

<img src="/static/img/etc/request_web.png" alt="Story Request | Web">

The storyteller, without needing to register or sign into an account, is routed to this private request page to gather the recording, transcript, and other information:

<img src="/static/img/etc/request_web_flow.png" alt="Story Request | Web Flow">

2. A request SMS and call:

> Rachelle is requesting an audio recording for "Grandma's Secret Recipe". When you are ready, please call +18005555555 and have this request ID ready: **12345**

The storyteller will call in, enter the request ID digits, and start speaking when prompted:

<img src="/static/img/etc/request_phone_flow.png" alt="Story Request | Phone Flow">

###### Processing Requests

As seen in the flow charts above, both requests handle the audio upload in similar ways, utilizing the unique Request ID (and the Twilio Call SID) to associate the newly created file and file path with the upload record created at the time of the request. With the help of Boto, Talkalog processes the audio blob and sends and stores the audio file in an Amazon S3 bucket.

___

### User Profile

<img src="/static/img/etc/user_profile.png" alt="User Profile">

The user profile interface showcases a list of the user's collections and associated uploads. Users are able to drag and drop, collapse, and edit titles inline thanks to jQuery Draggable/Droppable, Bootstrap Collapse, and X-Editable Bootstrap JavaScript.

___

### Transcripts

Text transcripts are generated either live during the recording if via web URL or at the requestor's discretion if the recording was captured over a phone call. All transcripts can be edited after the recording for accuracy and nice formatting using the rich text editor.

<img src="/static/img/etc/edit_transcript.png" alt="Edit Transcript">

___


<img src="/static/img/etc/data_model.png" alt="Talkalog Data Model" style="max-width: 100%;">