import jieba, string, boto3, json, os, hashlib
import gradio as gr
from botocore.exceptions import ClientError
from time import sleep

# Cards directory (hard-coded for now)
cardsdir = 'cards/'

# Global prompt (hard-coded for now)
prompt = '''Create flash cards to help an English speaker practice Chinese. 

Example input: 
你好
朋友

Output:
你好 | hello, nǐ hǎo
朋友 | friend, péng yǒu

Do not print anything except the requested output. Here is your input:
{}'''.strip() 

def make_cards(text):

    # Remove existing cards
    os.system('rm -rf {}'.format(cardsdir))

    # Remove existing .zip file
    os.system('rm -rf flashcards.zip')

    # Ensure that cards directory is present
    os.system('mkdir -p {}'.format(cardsdir))

    # Initialize a session using Amazon Polly
    polly_client = boto3.client('polly', region_name="us-west-2")
    
    # Create a Bedrock Runtime client in the AWS Region of your choice
    bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")

    word_list = process_chinese_text(text)

    # Generate flash cards with matching .mp3 files
    flashcard_list = []

    # We use a while loop as calls to Bedrock are frequently throttled,
    # necessitating retries
    num_words = len(word_list)
    i = 0
    while i < num_words:
        word = word_list[i]
        word_prompt = prompt.format(word)

        # Generate Anki-formatted flashcard entry
        try:
            result = invoke_claude_model(bedrock_client, word_prompt)
        except:
            print("Invoking model failed, sleeping for 5 seconds then re-trying")
            continue

        # Generate spoken word
        filename = synthesize_speech(polly_client, word, 'tmp.mp3')
        
        # Combine into single entry
        result += ' [sound:{}]'.format(filename)

        # Save to list
        flashcard_list.append(result)

        # Deal with Bedrock's aggressive throttling
        sleep(0.5)

        # Increment count
        i += 1

    # Write cards to file
    f = open(cardsdir + 'cards.txt', 'w')
    f.write("#separator:pipe\n")
    f.write("#html:true\n")
    for card in flashcard_list:
        f.write(card + '\n')
    f.close()

    # Use os.system to zip up the results and clean out the cards directory
    os.system('zip -r flashcards.zip {}'.format(cardsdir))
    os.system('rm -r {}/*'.format(cardsdir))

    return "flashcards.zip"

# Call polly on text
def synthesize_speech(polly_client, text, output_file):

    # Call the synthesize_speech API from Polly
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId='Zhiyu',  # Zhiyu is a Chinese Mandarin voice
        LanguageCode='cmn-CN'  # cmn-CN is the language code for Mandarin Chinese
    )

    # Save the audio stream returned by Amazon Polly into an mp3 file
    with open(cardsdir + output_file, 'wb') as file:
        file.write(response['AudioStream'].read())

    print(f"MP3 file saved temporarily as {output_file}")

    # Compute MD5 hash of the saved mp3 file
    md5_hash = compute_md5(cardsdir + output_file)

    # Rename the file to its MD5 hash with .mp3 extension
    new_filename = f"{md5_hash}.mp3"
    os.rename(cardsdir + output_file, cardsdir + new_filename)

    print(f"File renamed to {new_filename}")

    return new_filename

def compute_md5(file_path):
    # Compute and return the MD5 hash of a given file.
    md5 = hashlib.md5()
    
    with open(file_path, 'rb') as f:
        # Read in chunks to avoid memory issues with large files
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    
    return md5.hexdigest()

def invoke_claude_model(bedrock_client, prompt):

    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    # Convert the native request to JSON.
    request = json.dumps(native_request)

    try:
        # Invoke the model with the request.
        response = bedrock_client.invoke_model(modelId=model_id, body=request)

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)

    # Decode the response body.
    model_response = json.loads(response["body"].read())

    # Extract and print the response text.
    response_text = model_response["content"][0]["text"]

    return response_text

def process_chinese_text(text):
    # Define additional Chinese punctuation marks
    chinese_punctuation = '，。！？；：“”‘’（）【】《》、'
    
    # Combine English and Chinese punctuation
    all_punctuation = string.punctuation + chinese_punctuation
    
    # Remove all punctuation from text
    no_punct_text = ''.join(char for char in text if char not in all_punctuation)
    
    # Use jieba to segment the text into words
    segmented_words = jieba.lcut(no_punct_text)
    
    # Remove duplicates by converting to a set, then back to a list
    unique_words = list(set(segmented_words))
    
    return unique_words

demo = gr.Interface(
    fn=make_cards,
    inputs=[gr.Textbox(label="Input dialogue (Chinese)")],
    outputs=[gr.File(label="Flashcards")],
)

# Note: add root_path="/proxy/<port>" to .launch()
# when running on Coder IDE
demo.launch(root_path="/proxy/7860")
# demo.launch() # When running locally
# demo.launch() # When running locally and sharing globally