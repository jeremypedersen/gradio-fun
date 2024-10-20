import gradio as gr
from openai import OpenAI

def call_tts(key, speech):

    client = OpenAI(api_key=key)

    try:
        speech_file_path = "speech.mp3"
        response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=speech
        )

        response.stream_to_file(speech_file_path)
    except:
        speech_file_path = "oops.mp3" # Point at a default .mp3 with an error message

    return speech_file_path

demo = gr.Interface(
    fn=call_tts,
    inputs=[gr.Textbox(label="OpenAI API Key"), gr.Textbox(label="Text to speak")],
    outputs=[gr.Audio(label="Spoken Output")],
)

# Note: add root_path="/proxy/<port>" to .launch()
# when running on Coder IDE
demo.launch(root_path="/proxy/7860")
# demo.launch() # When running locally
# demo.launch() # When running locally and sharing globally
