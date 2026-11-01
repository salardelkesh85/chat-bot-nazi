# Local Semantic Memory

Nazi AI supports optional on-device semantic retrieval.

## Model
- Model: paraphrase-multilingual-MiniLM-L12-v2
- Languages: multilingual, including Persian support
- Model directory: backend/models/paraphrase-multilingual-MiniLM-L12-v2
- Runtime: sentence-transformers, CPU or supported local accelerator
- No hosted embedding API is called.

## Setup
1. Obtain the model files from the official Sentence Transformers / Hugging Face model repository.
2. Place the complete model folder at the path above.
3. Install optional dependencies with: pip install -r requirements-embeddings.txt
4. Restart the backend.

The application checks only the local model directory and uses local_files_only mode. It does not download model weights at runtime.

## Data
Each companion memory has an optional embedding JSON vector in SQLite. Vectors are created locally when a memory is saved. Chat retrieval compares the query vector with that companion's stored vectors. Memories without vectors remain eligible for lexical fallback.

## Privacy
Embedding generation runs on the local backend. No user message or memory is sent to a separate embedding service. Chat completion still follows the configured AI provider; if that provider is remote, chat prompt content leaves the device for response generation.
