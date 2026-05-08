"""
LLM Service — optimized for TinyLlama/TinyLlama-1.1B-Chat-v1.0
TinyLlama uses ChatML format: <|system|>, <|user|>, <|assistant|> tokens
"""
from typing import List, Dict
from app.core.config import get_settings
from app.core.logger import log

settings = get_settings()

_pipeline = None

FALLBACK_RESPONSE = (
    "I'm sorry, I couldn't find relevant information in the knowledge base "
    "to answer your question. Please try rephrasing, or ask an admin to "
    "upload related documents."
)


def _has_gpu() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def _get_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    log.info(f"Loading TinyLlama: {settings.llm_model_id}")
    from transformers import pipeline, AutoTokenizer
    import torch

    device = 0 if _has_gpu() else -1
    log.info(f"Device: {'GPU' if device == 0 else 'CPU'}")

    tokenizer = AutoTokenizer.from_pretrained(settings.llm_model_id)

    _pipeline = pipeline(
        "text-generation",
        model=settings.llm_model_id,
        tokenizer=tokenizer,
        device=device,
        torch_dtype=torch.float16 if _has_gpu() else torch.float32,
        trust_remote_code=True,
    )
    log.info("TinyLlama loaded successfully.")
    return _pipeline


def _build_chat_prompt(
    question: str,
    context_chunks: List[str],
    history: List[Dict],
) -> str:
    """
    TinyLlama uses ChatML format:
    <|system|>\n...<|endoftext|>\n
    <|user|>\n...<|endoftext|>\n
    <|assistant|>\n
    """
    context = "\n\n".join(context_chunks) if context_chunks else ""

    # System message
    if context:
        system_msg = (
            "You are a helpful assistant that answers questions strictly based "
            "on the provided knowledge base context. If the context does not "
            "contain enough information, say so clearly. Do not make up answers.\n\n"
            f"Knowledge Base Context:\n{context}"
        )
    else:
        system_msg = (
            "You are a helpful assistant. The user asked a question but no "
            "relevant information was found in the knowledge base. Politely "
            "inform the user that this topic is not covered in the knowledge "
            "base and suggest uploading relevant documents."
        )

    prompt = f"<|system|>\n{system_msg}<|endoftext|>\n"

    # Add conversation history (last 3 turns)
    for msg in history[-6:]:
        if msg["role"] == "user":
            prompt += f"<|user|>\n{msg['content']}<|endoftext|>\n"
        else:
            prompt += f"<|assistant|>\n{msg['content']}<|endoftext|>\n"

    # Current question
    prompt += f"<|user|>\n{question}<|endoftext|>\n<|assistant|>\n"

    return prompt


def generate_answer(
    question: str,
    context_chunks: List[str],
    history: List[Dict],
    in_knowledge_base: bool,
) -> str:
    if not in_knowledge_base:
        return FALLBACK_RESPONSE

    try:
        pipe = _get_pipeline()
        prompt = _build_chat_prompt(question, context_chunks, history)

        outputs = pipe(
            prompt,
            max_new_tokens=settings.max_new_tokens,
            temperature=settings.temperature,
            top_p=settings.top_p,
            do_sample=True,
            pad_token_id=pipe.tokenizer.eos_token_id,
            eos_token_id=pipe.tokenizer.eos_token_id,
            repetition_penalty=1.1,
        )

        full_output = outputs[0]["generated_text"]

        # Extract only the assistant's reply after the last <|assistant|>
        if "<|assistant|>" in full_output:
            answer = full_output.split("<|assistant|>")[-1].strip()
        else:
            answer = full_output[len(prompt):].strip()

        # Clean up any trailing tokens
        for stop in ["<|endoftext|>", "<|user|>", "<|system|>", "User:", "Human:"]:
            if stop in answer:
                answer = answer[:answer.index(stop)].strip()

        return answer if answer.strip() else FALLBACK_RESPONSE

    except Exception as e:
        log.error(f"TinyLlama generation error: {e}")
        return "I encountered an error generating a response. Please try again."