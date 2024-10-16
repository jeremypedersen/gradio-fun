import gradio as gr
from openai import OpenAI

def call_whisper(key, speech_path):

    client = OpenAI(api_key=key)

    try:
        speech_in = open(speech_path, 'rb')
        transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=speech_in
        )
        return transcription.text
    except:
        return "Something went wrong"

demo = gr.Interface(
    fn=call_whisper,
    inputs=[gr.Textbox(label="OpenAI API Key"), gr.Audio(label="Spoken Input", type="filepath")],
    outputs=[gr.Textbox(label="Transcript")]
)

# Note: add root_path="/proxy/<port>" to .launch()
# when running on Coder IDE
demo.launch(root_path="/proxy/7860")
# demo.launch() # When running locally
# demo.launch() # When running locally and sharing globally
