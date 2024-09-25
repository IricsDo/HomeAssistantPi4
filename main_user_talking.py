from llm.nvidia import VoiceAssistant
from python_lib import *

if __name__ == '__main__':
    # Define LLM model
    my_voice_assistant = VoiceAssistant()

    # Define speed-to-text model
    transcriber = aai.Transcriber()

    # Define input-output engine for text-to-speak
    engine = pyttsx3.init()
    r = sr.Recognizer()

   
    with sr.Microphone() as source:
        print("Calibrating...")
        r.adjust_for_ambient_noise(source, duration=5)
        # optional parameters to adjust microphone sensitivity
        # r.energy_threshold = 200
        # r.pause_threshold=0.5

        print("Okay, go!")
        while True:
            text = ""
            print("Listening now...")
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=30)
                print("Recognizing...")
                transcript = transcriber.transcribe(audio)
                if transcript.status == aai.TranscriptStatus.error:
                    print(transcript.error)
                else:
                    text = transcript.text
            except sr.RequestError as e:
                print("Could not request results {0}".format(e))
            except sr.UnknownValueError as e:
                print("unknown error occurred {0}".format(e))
            except Exception as e:
                unrecognized_speech_text = (
                    f"Sorry, I didn't catch that. Exception was: {e}s"
                )
                text = unrecognized_speech_text

                response = my_voice_assistant.CONVERSATION.invoke(
                    {"user_input": text}, 
                    config=my_voice_assistant.MY_CONFIG,
                )

                print(response.content)
                engine.say(response.content)
                engine.runAndWait()