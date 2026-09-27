import pyttsx3
engine = pyttsx3.init() # object creation

""" RATE"""
rate = engine.getProperty('rate')   # getting details of current speaking rate
print (rate)                        #printing current voice rate
engine.setProperty('rate', 110)     # setting up new voice rate


"""VOLUME"""
volume = engine.getProperty('volume')   #getting to know current volume level (min=0 and max=1)
print (volume)                          #printing current volume level
engine.setProperty('volume',0.3)    # setting up volume level  between 0 and 1

"""VOICE"""
voices = engine.getProperty('voices')       #getting details of current voice
#engine.setProperty('voice', voices[0].id)  #changing index, changes voices. o for male
engine.setProperty('voice', voices[29].id)   #changing index, changes voices. 1 for female
# for index, voice in enumerate(voices):
#     print(index, voice.id)  
    
engine.say("Hello World!")

engine.say('My current speaking rate is ' + str(rate))
engine.runAndWait()
engine.stop()

"""Saving Voice to a file"""
# On linux make sure that 'espeak' and 'ffmpeg' are installed
engine.save_to_file('Hello World', 'test.mp3')
engine.runAndWait()


# from gtts import gTTS
# from playsound import playsound

# greet = gTTS(text='Hello sir, how may I help you, sir.', lang='en')
# greet.save('output.mp3')
# playsound('output.mp3')
