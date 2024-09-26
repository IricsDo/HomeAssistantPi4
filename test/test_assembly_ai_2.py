# # Start by making sure the `assemblyai` package is installed.
# # If not, you can install it by running the following command:
# # pip install -U assemblyai
# #
# # Note: Some macOS users may need to use `pip3` instead of `pip`.

# import assemblyai as aai

# # Replace with your API key
# aai.settings.api_key = "bb2cca92ddd54c7b925480a530409138"

# # URL of the file to transcribe
# FILE_URL = "https://github.com/AssemblyAI-Community/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"

# # You can also transcribe a local file by passing in a file path
# # FILE_URL = './path/to/file.mp3'

# config = aai.TranscriptionConfig(speaker_labels=True)

# transcriber = aai.Transcriber()
# transcript = transcriber.transcribe(
#   FILE_URL,
#   config=config
# )

# for utterance in transcript.utterances:
#   print(f"Speaker {utterance.speaker}: {utterance.text}")
