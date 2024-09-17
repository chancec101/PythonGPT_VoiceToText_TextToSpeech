# Copyright © 2024 Chance Currie
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# as this was made for educational purposes and simply out of
# curiosity as OpenAI and Azure are both fascinating. Please see the
# GNU General Public License for more details, or view
# <https://www.gnu.org/licenses/> for more information.


# A Python program that connects to OpenAI's and Azure's API. 
# This program was run on a Windows machine in a Python 3.12 environment and utilizes ChatGPT 4o Mini, Azure Speech-to-Text, and Azure Text-to-Speech. 

# Importing the OpenAI API
from openai import OpenAI
# Importing the Azure API
import azure.cognitiveservices.speech as speechsdk

# The other libraries
import os 
import time
import tempfile
import subprocess
from pydub import AudioSegment
from pydub.playback import play

# Declaring the OpenAI key through calling the environment variable that we created back in Step 3 to keep the key a secret.
api_key = os.getenv('OPENAI_API_KEY')

# Validating OpenAI API key
if not api_key:
    exit("OpenAI API key is missing. Please set it in your environment variables.")

# Initializing the OpenAI client
client = OpenAI(api_key=api_key)

# A function that will generate a response based on what the user inputs
def chat_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content" : prompt}]
    )

    return response.choices[0].message.content.strip()

# The Azure Speech-To-Text manager
class SpeechToTextManager:
    azure_speechconfig = None
    azure_audioconfig = None
    azure_speechrecognizer = None

    def __init__(self):
        # Setting up the Azure Speech Configs
        try:
            self.azure_speechconfig = speechsdk.SpeechConfig(subscription=os.getenv('AZURE_TTS_KEY'), region=os.getenv('AZURE_TTS_REGION'))
        except TypeError:
            exit("Azure keys are missing! Please set AZURE_TTS_KEY and AZURE_TTS_REGION as environment variables!")

        if not self.azure_speechconfig:
            exit("Azure Speech SDK configuration failed.")

        self.azure_speechconfig.speech_recognition_language = "en-US"

    # Function to capture speech and convert it to text
    def speechtotext_from_mic(self):
        self.azure_audioconfig = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.azure_speechrecognizer = speechsdk.SpeechRecognizer(speech_config=self.azure_speechconfig, audio_config=self.azure_audioconfig)

        # Prompt to speak into your default microphone to get input capture
        print("Speak into your microphone...")
        speech_recognition_result = self.azure_speechrecognizer.recognize_once_async().get()

        # If the speech is recognized, it will translate it into text
        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            #print("Recognized: {}".format(speech_recognition_result.text))
            return speech_recognition_result.text
        # Else If the speech is not recognized, retry
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
            print("Retrying...")  # Add retry message
            return None  # Returning None here ensures the loop will prompt the user again
        # Else if the speech is cancelled for any reason, it will throw a cancellation message along with an error message if needed
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            print("Speech Recognition canceled: {}".format(speech_recognition_result.cancellation_details.reason))
            if speech_recognition_result.cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(speech_recognition_result.cancellation_details.error_details))

        return None

# The Azure Text-To-Speech manager
class TextToSpeechManager:
    def __init__(self):
        try:
            self.azure_speechconfig = speechsdk.SpeechConfig(subscription=os.getenv('AZURE_TTS2_KEY'), region=os.getenv('AZURE_TTS_REGION'))
        except TypeError:
            exit("Azure keys are missing! Please set AZURE_TTS2_KEY and AZURE_TTS_REGION as environment variables!")

        if not self.azure_speechconfig:
            exit("Azure Speech SDK configuration failed.")

        self.azure_speechconfig.speech_synthesis_voice_name = "en-US-AndrewMultilingualNeural"

    # Function to convert text to speech and play it
    def text_to_speech(self, text):

        audio_config = speechsdk.audio.AudioConfig(filename="output.wav")
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.azure_speechconfig, audio_config=audio_config)

        # Synthesize the text into speech and save it to the output.wav file
        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesis completed.")
            # Play the generated speech
            self.play_audio("output.wav")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")

    # Function to play the audio file
    def play_audio(self, file_path):
        try:
            # Redirect stderr to os.devnull to suppress the ffplay output since there's a lot of automatic logging that is done by that
            with open(os.devnull, 'wb') as devnull:
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", file_path],
                    check=True,
                    stderr=devnull
                )
        except Exception as e:
            print(f"An error occurred while playing audio: {e}")
        finally:
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    pass # Silent handling of errors if the file is in use

# A loop that will continue to run until user enters in a keyword that ends the program
if __name__ == "__main__":
    speech_manager = SpeechToTextManager()
    tts_manager = TextToSpeechManager()

    while True:
        try:
            speech_text = speech_manager.speechtotext_from_mic()
            
            if speech_text:
                print(f"\nUser: {speech_text}")

                chat_response = chat_gpt(speech_text)
                print(f"Bot: {chat_response}")

                tts_manager.text_to_speech(chat_response)
            else:
                print("No valid speech input detected. Please try again.")

            # Prompt the user to continue or quit
            user_exit = input("\nType 'quit' to exit or press Enter to continue: ").strip().lower()
            if user_exit == 'quit':
                break

            # Optional sleep to prevent rapid looping
            time.sleep(1)

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(1)