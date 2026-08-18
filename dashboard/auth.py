import hmac

import streamlit as st


def require_login():
    """
    Gate the current page behind a single shared password stored in
    st.secrets["APP_PASSWORD"]. Call this right after st.set_page_config()
    on every page - session_state is per-browser-session, so each page needs
    its own check (a user can navigate straight to a page URL).
    """
    if st.session_state.get("authenticated"):
        return

    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"], section[data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown("<div style='height:18vh'></div>", unsafe_allow_html=True)
        st.markdown("### Sign in")
        st.caption("This dashboard is restricted to authorized viewers.")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.button("Sign in", width="stretch")

        if submitted:
            correct = st.secrets.get("APP_PASSWORD", "")
            if correct and hmac.compare_digest(password, correct):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")

    st.stop()
