import gradio as gr
from openai import OpenAI

def call_gpt(prompt):

    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return completion.choices[0].message.content # Return first response

demo = gr.Interface(
    fn=call_gpt,
    inputs=[gr.Textbox(label="Prompt")],
    outputs=[gr.Textbox(label="Model output", show_copy_button=True)],
)

# Note: add root_path="/proxy/<port>" to .launch()
# when running on Coder IDE
demo.launch(root_path="/proxy/7860")
# demo.launch() # When running locally
# demo.launch() # When running locally and sharing globally
