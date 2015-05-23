from flask import Flask
import twilio.twiml

import os
from twilio.rest import TwilioRestClient

app = Flask(__name__)
 
Your Account Sid and Auth Token from twilio.com/user/account
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token  = os.environ['TWILIO_AUTH_TOKEN']
client = TwilioRestClient(account_sid, auth_token)
 
message = client.messages.create(body="Texting with Twilio!",
    to="+1xxxxxxxxxx",    # Replace with your phone number
    from_="+14153196892") # Replace with your Twilio number
print message.sid


# @app.route("/", methods=['GET', 'POST'])
# def hello_monkey():
#     """Respond to incoming requests."""
#     resp = twilio.twiml.Response()
#     resp.say("Hello world")
 
#     return str(resp)
 

if __name__ == "__main__":
    app.run(debug=True)