import os

# On Streamlit Community Cloud there is no .env file - config values are
# entered in the app's "Secrets" panel instead and exposed via st.secrets.
# Mirror them into os.environ (without overriding a real .env) so config.py's
# plain os.getenv(...) calls keep working unchanged in both places.
try:
    import streamlit as st

    for _key, _value in st.secrets.items():
        os.environ.setdefault(_key, str(_value))
except Exception:
    pass
