# FindBack AI

FindBack AI is a Streamlit-based lost-and-found platform that helps users report missing or recovered items, matches potential pairs using AI-powered similarity scoring, and manages claim resolution workflows with role-based access.

## Overview

The application combines:

- a SQLite-backed reporting system for lost and found items
- AI-assisted embedding and matching for candidate discovery
- provider-based LLM analysis for item feature extraction
- authentication and permissions for admin, staff, and regular users
- claim handling for verified handovers and item resolution

## Features

- Report lost or found items with title, description, category, color, location, date, and optional image
- AI-based item analysis and feature extraction using Groq or Hugging Face providers
- Semantic match scoring with FAISS-based retrieval and rule-based fallback
- Dashboard with summary counters for report volume and potential matches
- Role-based access control for users, staff, and administrators
- Claim workflow to approve or resolve a lost-found match
- Demo user accounts for quick testing

## Project Structure

```text
findback-ai/
├── app.py                       # Streamlit application entry point
├── auth.py                     # Authentication and permissions
├── requirements.txt            # Python dependencies
├── ai/                         # Embedding and provider logic
│   ├── embeddings.py
│   ├── groq_provider.py
│   ├── huggingface_provider.py
│   ├── matcher.py
│   ├── prompts.py
│   ├── provider.py
│   └── schemas.py
├── components/                 # UI theme and reusable visual components
├── database/                  # SQLite schema and query layer
│   ├── database.py
│   └── queries.py
├── services/                  # Business logic for items, matching, claims, and providers
│   ├── claim_service.py
│   ├── image_service.py
│   ├── item_service.py
│   ├── matching_service.py
│   └── provider_service.py
├── utils/                     # Security, validation, time, and location utilities
├── tests/                     # Automated tests for auth and claims
├── vector_store/               # FAISS index and metadata
├── data/                      # Sample report data folders
├── findbackAI_env/            # Local virtual environment
├── findback.db                # SQLite database generated at runtime
└── README.md                  # Project documentation
```

## Tech Stack

- Python 3.12
- Streamlit
- SQLite
- Sentence Transformers
- FAISS
- Pillow
- Pydantic
- PyTorch
- NumPy

## Prerequisites

- Python 3.10+
- A virtual environment is recommended
- Optional AI API credentials for Groq or Hugging Face

## Setup

1. Open a terminal in the project folder.
2. Activate the workspace virtual environment:

   Windows PowerShell:

   ```powershell
   .\findbackAI_env\Scripts\Activate.ps1
   ```

   Windows Command Prompt:

   ```bat
   findbackAI_env\Scripts\activate.bat
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Optional: configure AI keys in a Streamlit secrets file for app-level AI access.

   Create `.streamlit/secrets.toml` with content like:

   ```toml
   [GROQ]
   API_KEY = "your_groq_api_key"
   ```

   or:

   ```toml
   [HUGGINGFACE]
   API_KEY = "your_huggingface_api_key"
   ```

## Run the Application

From the project root:

```bash
streamlit run app.py
```

Then open the local URL displayed in the terminal, usually:

```text
http://localhost:8501
```

## Demo Accounts

The application seeds demo accounts automatically on first run:

| Username | Password | Role |
| --- | --- | --- |
| admin | Admin@123 | Administrator |
| staff | Staff@123 | Staff |
| user1 | User@123 | Regular User |
| user2 | User@123 | Regular User |
| user3 | User@123 | Regular User |

## Usage

1. Sign in with a demo account.
2. Navigate to "Report Lost" or "Report Found" to create an item report.
3. Use the matching workflow to discover likely pairings for lost items.
4. Review and resolve claims as staff or admin.
5. Adjust provider settings under the app settings area if you want to use a different AI provider or personal key.

## Testing

Run the automated tests with:

```bash
pytest
```

The current test suite covers default user seeding and claim resolution logic.

## Notes

- The application auto-creates its SQLite database on launch if it does not already exist.
- Matching uses semantic similarity and weighted scoring across text, category, location, time, and image signals.
- If no AI provider is available, the app falls back to a lightweight rule-based extractor.

## License

This project is currently provided for internal or educational use without a formal license file.
