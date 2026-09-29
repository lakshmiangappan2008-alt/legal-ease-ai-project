import os
from datetime import date

import requests
import streamlit as st

from dotenv import load_dotenv

from utils.document_formatter import (
    format_docx,
    format_html_preview,
    format_pdf,
    format_txt,
)


load_dotenv()


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="wide",
)


# --------------------------------------------------
# BACKEND CONFIGURATION
# --------------------------------------------------

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>

    .hero {
        padding: 1.5rem;
        border-radius: 16px;
        background: linear-gradient(
            135deg,
            #111827,
            #1f2937
        );
        color: white;
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin-bottom: 0.2rem;
    }

    .hero p {
        margin-bottom: 0;
        opacity: 0.85;
    }

    .preview {
        background: #111827;
        color: #f3f4f6;
        border-radius: 12px;
        padding: 1.5rem;
        max-height: 650px;
        overflow-y: auto;
        line-height: 1.7;
    }

    .preview p {
        margin-bottom: 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">

        <h1>⚖️ LegalEase</h1>

        <p>
        AI-assisted legal document drafting,
        editing and export.
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


st.info(
    "LegalEase creates AI-assisted drafts for "
    "document preparation. Review the generated "
    "document with a qualified legal professional "
    "before relying on it."
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "document" not in st.session_state:

    st.session_state.document = ""


if "document_type" not in st.session_state:

    st.session_state.document_type = ""


# --------------------------------------------------
# INPUT FORM
# --------------------------------------------------

with st.form(
    "legal_document_form"
):

    left_column, right_column = (
        st.columns(2)
    )

    # ----------------------------------------------
    # LEFT COLUMN
    # ----------------------------------------------

    with left_column:

        document_type = st.text_input(
            "Document Type",
            value=(
                st.session_state.document_type
            ),
            placeholder=(
                "Example: Freelance Work Contract"
            ),
        )

        parties = st.text_area(
            "Parties Involved",
            placeholder=(
                "Jane Doe (Service Provider), "
                "TechNova Inc. (Client)"
            ),
            height=120,
        )

        effective_date = st.text_input(
            "Effective Date",
            value=(
                date.today().strftime(
                    "%B %d, %Y"
                )
            ),
        )

    # ----------------------------------------------
    # RIGHT COLUMN
    # ----------------------------------------------

    with right_column:

        terms_raw = st.text_area(
            "Terms & Conditions",
            placeholder=(
                "Payment within 30 days; "
                "Confidentiality must be maintained; "
                "Either party may terminate with "
                "15 days notice"
            ),
            height=120,
            help=(
                "Separate individual terms using "
                "semicolons."
            ),
        )

        jurisdiction = st.text_input(
            "Jurisdiction",
            placeholder=(
                "Example: Tamil Nadu, India"
            ),
        )

        additional_instructions = (
            st.text_area(
                "Additional Instructions",
                placeholder=(
                    "Optional special drafting "
                    "instructions..."
                ),
                height=120,
            )
        )

    # ----------------------------------------------
    # GENERATE BUTTON
    # ----------------------------------------------

    generate_button = (
        st.form_submit_button(
            "✨ Generate Document",
            type="primary",
            use_container_width=True,
        )
    )


# --------------------------------------------------
# GENERATE DOCUMENT
# --------------------------------------------------

if generate_button:

    if not document_type.strip():

        st.error(
            "Please enter a document type."
        )

    elif not parties.strip():

        st.error(
            "Please enter the parties involved."
        )

    elif not terms_raw.strip():

        st.error(
            "Please enter at least one term."
        )

    else:

        terms = [
            term.strip()
            for term in terms_raw.split(";")
            if term.strip()
        ]

        payload = {

            "document_type":
                document_type.strip(),

            "parties":
                parties.strip(),

            "terms":
                terms,

            "effective_date":
                effective_date.strip(),

            "jurisdiction":
                jurisdiction.strip(),

            "additional_instructions":
                additional_instructions.strip(),
        }

        try:

            with st.spinner(
                "Generating your legal document..."
            ):

                response = requests.post(
                    f"{BACKEND_URL}/generate",
                    json=payload,
                    timeout=180,
                )

            if response.ok:

                data = response.json()

                st.session_state.document = (
                    data["content"]
                )

                st.session_state.document_type = (
                    data["document_type"]
                )

                st.success(
                    "Document generated successfully."
                )

            else:

                try:

                    error_message = (
                        response.json()
                        .get(
                            "detail",
                            response.text,
                        )
                    )

                except Exception:

                    error_message = (
                        response.text
                    )

                st.error(
                    f"Backend error "
                    f"({response.status_code}): "
                    f"{error_message}"
                )

        except requests.RequestException as exc:

            st.error(
                "Could not connect to the FastAPI "
                "backend.\n\n"
                f"Backend URL: {BACKEND_URL}\n\n"
                f"Error: {exc}"
            )


# --------------------------------------------------
# GENERATED DOCUMENT
# --------------------------------------------------

if st.session_state.document:

    st.divider()

    st.subheader(
        "📄 Document Preview"
    )

    preview_html = (
        format_html_preview(
            st.session_state.document
        )
    )

    st.markdown(
        f"""
        <div class="preview">
            {preview_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ----------------------------------------------
    # EDITOR
    # ----------------------------------------------

    st.subheader(
        "✏️ Edit Document"
    )

    edited_document = st.text_area(
        "Edit the generated document",
        value=(
            st.session_state.document
        ),
        height=600,
        label_visibility="collapsed",
    )

    st.session_state.document = (
        edited_document
    )

    # ----------------------------------------------
    # EXPORT
    # ----------------------------------------------

    st.subheader(
        "⬇️ Download Document"
    )

    col1, col2, col3 = (
        st.columns(3)
    )

    txt_data = format_txt(
        edited_document
    )

    docx_data = format_docx(
        edited_document,
        st.session_state.document_type,
    )

    pdf_data = format_pdf(
        edited_document,
        st.session_state.document_type,
    )

    safe_filename = "".join(
        character.lower()
        if character.isalnum()
        else "_"
        for character
        in st.session_state.document_type
    ).strip("_")

    if not safe_filename:

        safe_filename = (
            "legalease_document"
        )

    # ----------------------------------------------
    # TXT
    # ----------------------------------------------

    with col1:

        st.download_button(
            label="⬇️ Download TXT",
            data=txt_data,
            file_name=(
                f"{safe_filename}.txt"
            ),
            mime="text/plain",
            use_container_width=True,
        )

    # ----------------------------------------------
    # DOCX
    # ----------------------------------------------

    with col2:

        st.download_button(
            label="⬇️ Download DOCX",
            data=docx_data,
            file_name=(
                f"{safe_filename}.docx"
            ),
            mime=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            use_container_width=True,
        )

    # ----------------------------------------------
    # PDF
    # ----------------------------------------------

    with col3:

        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_data,
            file_name=(
                f"{safe_filename}.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
        )


st.divider()

st.caption(
    "LegalEase • AI-assisted document drafting • "
    "Review generated documents before use."
)