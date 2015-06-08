# Talkalog

Talkalog is the easiest way to create, request, and store audio recordings. Have your grandmother record her coveted secret family recipes, generate and edit the transcripts, and have a readymade recipe book instantly.

#### Technology Stack

JavaScript, jQuery, HTML, Sass, Bootstrap, Python, Flask, Jinja, SQLAlchemy, SQLite, Amazon Web Services S3, Boto

#### APIs

<a href="http://twilio.com/" target="_blank">Twilio SMS and Voice</a>, <a href="https://developers.google.com/web/updates/2013/01/Voice-Driven-Web-Apps-Introduction-to-the-Web-Speech-API?hl=en" target="_blank">Web Speech</a> / <a href="https://pypi.python.org/pypi/SpeechRecognition/" target="_blank">Speech Recognition</a>, <a href="https://github.com/mattdiamond/Recorderjs" target="_blank">Recorder.js</a>, <a href="https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API" target="_blank">HTML5 Web Audio</a>

## Overview

In most scenarios, Talkalog has two user roles: the _requestor_ and _storyteller_.

#### User Story Example:
1. Requestor logs in and makes a request
2. Request is sent to storyteller via URL or SMS
3. Storyteller arrives at Request URL or call
4. Storyteller is prompted to begin recording 
5. Recording is saved and routed into requestor's Talkalog account
6. Requestor can now control permissions and sharing, transcript formatting, and more