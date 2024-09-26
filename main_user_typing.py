from llm.nvidia import VoiceAssistant
from packagelib import *

if __name__ == '__main__':
    print("Plese wait to setup assistant ...!")

    try:
        # Define LLM model
        my_voice_assistant = VoiceAssistant()

        # Define input-output engine for text-to-speak
        engine = pyttsx3.init()
        engine.setProperty('rate', 200)
        engine.setProperty('volume', 0.4)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[29].id)

        print("Okay, go!")
        engine.say("Hi Iris!")
        engine.runAndWait()

        while True:
            text = input("What would you want to say with me?\n> ")
            if not text:
                engine.say("Sorry, I don't understand you!")
                engine.runAndWait()
            elif text == 'q':
                break
            else:
                response = my_voice_assistant.CONVERSATION.invoke(
                    {"user_input": text}, 
                    config=my_voice_assistant.MY_CONFIG,
                )
                print(f"${response.content}")
                engine.say(response.content)
                engine.runAndWait()
        engine.stop()

    except Exception as e:
        print(e)
    finally:
        engine.say("Bye Iris!")
        engine.runAndWait()
        print("Shutdown assistant !")
