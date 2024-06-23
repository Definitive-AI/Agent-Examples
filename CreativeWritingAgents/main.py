from pathlib import Path

import streamlit as st
from st_pages import Page, show_pages, add_page_title

#with st.echo("below"):
#"## AI Agents"

show_pages(
    [
        Page("main.py", "AI Agents", "🏠"),
        Page("graph.py", "Graph - Content Creation Team"),
        Page("agents.py", "Agent - Content Creation Team"),
    ]
)

add_page_title()  # Optional method to add title and icon to current page
