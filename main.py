
# pyright: reportMissingImports=false
# ruff: noqa: I001

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile  # ty: ignore[unresolved-import]
from fastapi.responses import HTMLResponse  # ty: ignore[unresolved-import]
from fastapi.staticfiles import StaticFiles  # ty: ignore[unresolved-import]
from fastapi.templating import Jinja2Templates  # pyright: ignore[reportMissingImports]  # ty: ignore[unresolved-import]
from pydantic import BaseModel  # ty: ignore[unresolved-import]

from .services.ai_service import ask_legal_ai, summarize_text
from .services.document_service import extract_text_from_file


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="LegalEaseAI",
    description="AI-powered legal information assistant",
    version="1.0.0",
)


# Static files
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)


# HTML templates
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


class QuestionRequest(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "message": "LegalEaseAI is running"
    }


@app.post("/api/ask")
async def ask_question(data: QuestionRequest):

    question = data.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a legal question."
        )

    try:
        answer = ask_legal_ai(question)

        return {
            "success": True,
            "question": question,
            "answer": answer
        }

    except (OSError, ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"AI error: {error!s}"
        )


@app.post("/api/summarize")
async def summarize_document(
    file: UploadFile | None = None,
    _: None = File(None)
):
    if file is None:
        raise HTTPException(
            status_code=400,
            detail="No file was uploaded."
        )

    filename = file.filename or "document"

    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt"
    }

    extension = Path(filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX and TXT files are supported."
        )

    file_data = await file.read()

    if not file_data:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    try:

        text = extract_text_from_file(
            filename,
            file_data
        )

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text was found in the document."
            )

        summary = summarize_text(text)

        return {
            "success": True,
            "filename": filename,
            "summary": summary
        }

    except HTTPException:
        raise

    except (OSError, ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing error: {error!s}"
        )