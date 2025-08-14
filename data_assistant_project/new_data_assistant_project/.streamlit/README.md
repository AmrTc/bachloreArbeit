# Local Streamlit Configuration

This directory contains local Streamlit configuration files for development.

## Files

- `config.toml` - Streamlit application configuration (committed to git)
- `secrets.toml` - Local secrets (NOT committed to git)

## Setup Local Development

1. **Copy the template:**
   ```bash
   cp .streamlit/secrets.toml.template .streamlit/secrets.toml
   ```

2. **Edit `.streamlit/secrets.toml`:**
   ```toml
   # Replace with your actual API key
   ANTHROPIC_API_KEY = "sk-ant-api03-..."
   ```

3. **Never commit `secrets.toml` to git!**
   - It's already in `.gitignore`
   - Contains sensitive information

## Configuration Priority

The application reads the API key in this order:
1. **Streamlit Cloud secrets** (production)
2. **Local `.streamlit/secrets.toml`** (development)
3. **Environment variables** (fallback)

## Testing

Run locally to test:
```bash
cd new_data_assistant_project
streamlit run streamlit_entry.py
```

The app will automatically use your local `secrets.toml` configuration.
