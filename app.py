import os
import time
import openai
import gpt_index
import PyPDF2
import pickle
import urllib.request
from flask import Flask, request, jsonify
from ratelimit import limits, sleep_and_retry

app = Flask(__name__)

# Set up OpenAI API key and GPT-3 engine
openai.api_key = os.environ.get('OPENAI_API_KEY')
gpt3_engine = os.environ.get('GPT3_ENGINE', 'davinci')

# Define rate limits for OpenAI API requests
OPENAI_RATE_LIMIT = int(os.environ.get('OPENAI_RATE_LIMIT', 0))
OPENAI_RATE_PERIOD = int(os.environ.get('OPENAI_RATE_PERIOD', 1))

# Define rate limits for local requests
LOCAL_RATE_LIMIT = int(os.environ.get('LOCAL_RATE_LIMIT', 0))
LOCAL_RATE_PERIOD = int(os.environ.get('LOCAL_RATE_PERIOD', 1))

# Function to generate embeddings and build index for a document
@sleep_and_retry
@limits(calls=OPENAI_RATE_LIMIT, period=OPENAI_RATE_PERIOD)
def generate_embeddings(paragraphs):
    embeddings = []
    for paragraph in paragraphs:
        response = openai.Completion.create(
            engine=gpt3_engine,
            prompt=paragraph,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )
        embedding = response.choices[0].embedding
        embeddings.append(embedding)
    return embeddings

def build_document_index(document_path):
    cache_path = os.path.join(os.path.dirname(document_path), 'cache.pkl')

    # Check if cached embeddings and search index exist
    try:
        with open(cache_path, 'rb') as cache_file:
            cached_data = pickle.load(cache_file)
            document_embeddings = cached_data['embeddings']
            local_gpt_index = cached_data['index']
    except FileNotFoundError:
        # If cache file does not exist, generate embeddings and build index
        pdf_file = open(document_path, 'rb')
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        document_text = ''
        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            document_text += page.extractText()
        pdf_file.close()

        document_paragraphs = document_text.split('\n\n')

        if OPENAI_RATE_LIMIT > 0:
            # Throttle API requests with rate limits
            document_embeddings = []
            for i in range(0, len(document_paragraphs), OPENAI_RATE_LIMIT):
                embeddings = generate_embeddings(document_paragraphs[i:i+OPENAI_RATE_LIMIT])
                document_embeddings.extend(embeddings)
                time.sleep(OPENAI_RATE_PERIOD)
        else:
            # Make API requests without rate limits
            document_embeddings = generate_embeddings(document_paragraphs)

        local_gpt_index = gpt_index.GptIndex(gpt3_engine)
        local_gpt_index.add(document_embeddings)

        # Cache the embeddings and search index
        cached_data = {'embeddings': document_embeddings, 'index': local_gpt_index}
        with open(cache_path, 'wb') as cache_file:
            pickle.dump(cached_data, cache_file)

    return local_gpt_index

# Function to search the cached document index
def search_document_index(document_path, search_query):
    cache_path = os.path.join(os.path.dirname(document_path), 'cache.pkl')

    # Load cached embeddings and search index
    with open(cache_path, 'rb') as cache_file:
        cached_data = pickle.load(cache_file)
        local_gpt_index = cached_data
    # Search the index for matching paragraphs
    if LOCAL_RATE_LIMIT > 0:
        # Throttle local requests with rate limits
        matching_paragraphs = []
        for i, embedding in enumerate(cached_data['embeddings']):
            if i % LOCAL_RATE_LIMIT == 0:
                time.sleep(LOCAL_RATE_PERIOD)
            if local_gpt_index.search(embedding, search_query):
                matching_paragraphs.append(i)
    else:
        # Make local requests without rate limits
        matching_paragraphs = [i for i, embedding in enumerate(cached_data['embeddings']) if local_gpt_index.search(embedding, search_query)]

    # Retrieve matching text from the document
    pdf_file = open(document_path, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    matching_text = ''
    for paragraph_num in matching_paragraphs:
        page_num = 0
        while paragraph_num >= pdf_reader.getPage(page_num).getNumWords()/25:
            paragraph_num -= pdf_reader.getPage(page_num).getNumWords()/25
            page_num += 1
        paragraph_text = pdf_reader.getPage(page_num).extractText().split('\n\n')[int(paragraph_num)]
        matching_text += paragraph_text + '\n\n'

    pdf_file.close()
    return matching_text

# Endpoint to create or refresh and store new index
@app.route('/build_index', methods=['POST'])
def build_index():
    auth_token = request.headers.get('Authorization')
    if not auth_token or auth_token != 'Bearer YOUR_BEARER_TOKEN':
        response = {'message': 'Authentication failed.'}
        return jsonify(response), 401

    document_url = request.json['url']
    document_path = os.path.basename(document_url)

    # Download the document from URL or use local path
    if document_url.startswith('http'):
        urllib.request.urlretrieve(document_url, document_path)
    else:
        document_path = os.path.join('path/to/documents', document_path)

    local_gpt_index = build_document_index(document_path)

    response = {'message': 'Index built and cached successfully.'}
    return jsonify(response), 200

# Endpoint to search the cached document index
@app.route('/search_index', methods=['POST'])
def search_index():
    auth_token = request.headers.get('Authorization')
    if not auth_token or auth_token != 'Bearer YOUR_BEARER_TOKEN':
        response = {'message': 'Authentication failed.'}
        return jsonify(response), 401

    document_url = request.json['url']
    search_query = request.json['query']
    document_path = os.path.basename(document_url)

    # Download the document from URL or use local path
    if document_url.startswith('http'):
        urllib.request.urlretrieve(document_url, document_path)
    else:
        document_path = os.path.join('path/to/documents', document_path)

    matching_text = search_document_index(document_path, search_query)

    response = {'matching_text': matching_text}
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True)
