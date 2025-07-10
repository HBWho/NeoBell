# Centralized TTS phrases for NeoBell

MAIN_LOOP = {
    "greeting": "Hi, I'm NeoBell. Do you want to deliver a package or to leave a message?",
    "unclear_intent": "Sorry, I didn't get that. Please say 'delivery' or 'message'.",
    "error": "Something went wrong. Let's start over.",
}

VISITOR = {
    "start": "Hi! Please look at the camera.",
    "face_recognition": "Analyzing your face, please hold still for a moment.",
    "known_hello": "Hello {visitor_name}, checking your access.",
    "allowed": "You can leave a message.",
    "recording": "You will have 10 seconds to leave your message. Starting in 3, 2, 1.",
    "done": "Done! Sending your message.",
    "sent": "Message sent. Thank you!",
    "not_send": "Sorry, I couldn't send your message. Please try again later.",
    "denied": "Sorry {visitor_name}, you can't leave a message now.",
    "perm_error": "Sorry, I couldn't check your access. Please contact support.",
    "unknown": "I don't recognize you. Would you like to register?",
    "register_no": "Have a nice day!",
    "register_yes": "Great! What's your name?",
    "register_name_fail": "Sorry, I didn't get your name. Please try again later.",
    "register_profile_fail": "Sorry, there was a problem creating your profile.",
    "register_photo_wo_lighting": "I will now take several photos. First, with normal lighting.",
    "register_photo_w_lighting": "Now, I will use a flash for the next set of photos.",
    "register_photo_complete": "Thank you. Processing your images now, please wait a moment.",
    "register_complete": "All set! Registration complete.",
    "register_error": "Sorry, there was a problem during registration.",
    "system_error": "Sorry, there was a system error. Please try again later.",
    "profile_issue": "There is an issue with your profile. Let's try registering again.",
    "perm_later": "Couldn't check your permissions now. Please try later.",
    "ask_message": "Would you like to leave a message?",
    "recognition_fail": "I'm sorry, I couldn't see anyone clearly.",
    "ask_retry": "Would you like to try again?",
    "confirm_retry": "Okay, let's try one more time. Please look straight at the camera.",
    "max_retries_fail": "I'm still having trouble seeing a face. If you would like to try again, press the main button to start over."
}

DELIVERY = {
    "start": "Please show the package code to the camera.",
    "not_accepted": "This package isn't registered. Try another?",
    "timeout": "Couldn't read the code. Try again?",
    "compartment": "Delivery authorized. Please place the package inside the compartment, label facing up.",
    "checking": "Checking the package.",
    "internal_fail": "Couldn't verify the code inside. Try again?",
    "internal_adjust": "Adjust the package inside the compartment, making sure the label is facing up.",
    "finalize": "Package received. Thank you!",
    "error": "Something went wrong. Please try again.",
    "cancel": "Okay, have a nice day!",
    "cancel_inside": "Okay, remove the package from inside, close the door and have a nice day!",
}

YESNO = {
    "clarify": "I'm sorry, I didn't quite catch that. Could you please clarify?",
    "affirmative": "Okay!",
    "negative": "Alright.",
    "not_understood": "I'm sorry, I didn't quite catch that. Could you please clarify?",
    "max_attempts": "Sorry, I couldn't understand after several tries. Let's try again later.",
    "conflict": "I heard both yes and no. Let's try again.",
}
