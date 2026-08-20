"""Local Gradio interface for evaluating portfolio-grounded answers."""

from __future__ import annotations

from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

from app.chat_service import (
    ChromaPortfolioRetriever,
    ChatService,
    MAX_MESSAGE_CHARACTERS,
    MESSAGE_LENGTH_ERROR,
    STARTER_QUESTIONS,
    WELCOME_TEXT,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHAT_INPUT_ELEMENT_ID = "portfolio-chat-input"


def validate_chat_message(message: str | None) -> dict[str, object]:
    """Reject over-limit browser submissions before Gradio adds them to chat history."""
    return gr.validate(
        len(message or "") <= MAX_MESSAGE_CHARACTERS,
        MESSAGE_LENGTH_ERROR,
    )


def _chat_input_limit_script() -> str:
    """Keep the local input limit and counter in sync without a server round trip."""
    return f"""
() => {{
  const limit = {MAX_MESSAGE_CHARACTERS};
  const errorMessage = {MESSAGE_LENGTH_ERROR!r};

  const attachInputLimit = () => {{
    const container = document.getElementById("{CHAT_INPUT_ELEMENT_ID}");
    const input = container?.querySelector("textarea, input");
    if (!input || input.dataset.messageLimitAttached) return Boolean(input);

    input.dataset.messageLimitAttached = "true";
    const counter = document.createElement("div");
    counter.setAttribute("aria-live", "polite");
    counter.style.cssText = "font-size: 0.8rem; margin-top: 0.25rem;";
    input.insertAdjacentElement("afterend", counter);

    const setError = (message = "") => {{
      input.setCustomValidity(message);
      counter.textContent = message || `${{Array.from(input.value).length}} / ${{limit}}`;
    }};
    const prospectiveLength = (insertedText) => {{
      const start = input.selectionStart ?? input.value.length;
      const end = input.selectionEnd ?? input.value.length;
      return Array.from(input.value.slice(0, start) + insertedText + input.value.slice(end)).length;
    }};

    input.addEventListener("beforeinput", (event) => {{
      if (event.inputType.startsWith("insert") && event.data && prospectiveLength(event.data) > limit) {{
        event.preventDefault();
        setError(errorMessage);
      }}
    }});
    input.addEventListener("paste", (event) => {{
      const pastedText = event.clipboardData?.getData("text") || "";
      if (prospectiveLength(pastedText) > limit) {{
        event.preventDefault();
        setError(errorMessage);
      }}
    }});
    input.addEventListener("input", () => setError());
    setError();
    return true;
  }};

  if (attachInputLimit()) return;
  const observer = new MutationObserver(() => {{
    if (attachInputLimit()) observer.disconnect();
  }});
  observer.observe(document.body, {{ childList: true, subtree: true }});
}}
"""


def create_app() -> gr.Blocks:
    """Build the interface without placing welcome text in chat history."""
    load_dotenv(PROJECT_ROOT / ".env")
    service = ChatService(ChromaPortfolioRetriever(PROJECT_ROOT))
    with gr.Blocks(
        title="Ace's Portfolio AI Assistant",
        js=_chat_input_limit_script(),
    ) as app:
        gr.Markdown(WELCOME_TEXT)
        textbox = gr.Textbox(
            max_length=MAX_MESSAGE_CHARACTERS,
            show_label=False,
            container=False,
            elem_id=CHAT_INPUT_ELEMENT_ID,
            render=False,
        )
        gr.ChatInterface(
            fn=service.respond,
            examples=STARTER_QUESTIONS,
            type="messages",
            fill_height=True,
            textbox=textbox,
            validator=validate_chat_message,
        )
    return app


if __name__ == "__main__":
    create_app().launch(server_name="127.0.0.1", share=False, inbrowser=True)
