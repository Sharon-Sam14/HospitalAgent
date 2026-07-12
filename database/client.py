"""
Supabase client singleton.
Reads credentials from Streamlit secrets (or environment variables as fallback).
"""
from __future__ import annotations

import os
from functools import lru_cache

from supabase import create_client, Client


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Return a cached Supabase client instance."""
    try:
        # Prefer Streamlit secrets when running inside the app
        import streamlit as st
        url: str = st.secrets["SUPABASE_URL"]
        key: str = st.secrets["SUPABASE_KEY"]
    except Exception:
        # Fallback for standalone scripts (seed.py, tests)
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]

    return create_client(url, key)
