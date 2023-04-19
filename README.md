# Document Search with GPT-3 and OpenAI API

This Flask app uses GPT-3 and the OpenAI API to generate embeddings and build a search index for a PDF document, and allows users to search for specific text within the document. The app uses a shared Docker volume to cache the embeddings and search index for faster searching.

## Installation and Setup

1. Clone the repository to your local machine.
2. Install Docker and Docker Compose if you don't already have them installed.
3. Set your OpenAI API key and GPT-3 engine in the `docker-compose.yml` file.
4. Start the app using `docker-compose up`.

## Endpoints

### `POST /build_index`

Builds or refreshes the search index for a document and caches it in the shared Docker volume.

#### Request Body

```
{
  "url": "https://example.com/my-document.pdf"
}
```

#### Response

```
{
  "message": "Index built and cached successfully."
}
```

### `POST /search_index`

Searches the cached search index for a document for a specific query.

#### Request Body

```
{
  "url": "https://example.com/my-document.pdf",
  "query": "search query"
}
```

#### Response

```
{
  "matching_text": "matching text"
}
```

## Environment Variables

The following environment variables can be set in the `docker-compose.yml` file:

- `OPENAI_API_KEY`: Your OpenAI API key.
- `GPT3_ENGINE`: The GPT-3 engine to use (default: `davinci`).
- `OPENAI_RATE_LIMIT`: The rate limit for OpenAI API requests (default: `0`).
- `OPENAI_RATE_PERIOD`: The rate limit period in seconds for OpenAI API requests (default: `1`).
- `LOCAL_RATE_LIMIT`: The rate limit for local requests (default: `0`).
- `LOCAL_RATE_PERIOD`: The rate limit period in seconds for local requests (default: `1`).

## Authentication

Endpoints are protected by bearer token authentication. The bearer token must be included in the `Authorization` header of the request. The token can be set in the `build_index` and `search_index` functions in the `app.py` file.

