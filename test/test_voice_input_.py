import speech_recognition as sr

# Replace with the correct device index (225 in your case)
device_index = 225

# Initialize recognizer
r = sr.Recognizer()

# Use the USB microphone
with sr.Microphone(device_index=device_index) as source:
    print("Say something!")
    audio = r.listen(source)

# Recognize speech using Google API or other services
try:
    print("Google Speech Recognition thinks you said: " + r.recognize_google(audio))
except sr.UnknownValueError:
    print("Google could not understand audio")
except sr.RequestError as e:
    print(f"Could not request results from Google; {e}")
