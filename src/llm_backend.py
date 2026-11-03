"""Optional real-model backend: Qwen2.5-0.5B-Instruct on CPU.

This follows the experiment pattern of Part 1 of the series
("Demystifying LLM Reasoning"), which ran the same small open model
because its full internals are accessible and it runs on a laptop CPU.

The lab's core suite never imports this module's heavy dependencies at
import time and never requires a download: ``available()`` reports why
the backend cannot run, and callers degrade gracefully. To use it:

    pip install transformers torch        # CPU wheels are enough
    python3 src/r1_direct_vs_cot.py --llm

The R1-R3 tasks share one sampling pass over this backend (see
``llm_experiment.py``): per problem, one greedy direct answer plus k
sampled chains-of-thought, so the direct / single-chain / majority-vote /
verifier numbers all describe the *same* generations.

The first run downloads the model (~1 GB) from Hugging Face; afterwards
it is cached locally.
"""

from __future__ import annotations

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

_cache = {}


def available():
    """Return (ok, reason). Never raises."""
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except Exception as exc:  # ImportError or a broken native library
        return False, f"transformers/torch not importable ({type(exc).__name__})"
    return True, "ok"


def _load():
    if "model" not in _cache:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, torch_dtype=torch.float32)
        model.eval()
        _cache["tok"], _cache["model"] = tok, model
    return _cache["tok"], _cache["model"]


def _generate(prompt: str, max_new_tokens: int, do_sample: bool,
              temperature: float = 0.0, seed=None) -> str:
    import torch

    tok, model = _load()
    messages = [{"role": "user", "content": prompt}]
    text = tok.apply_chat_template(messages, tokenize=False,
                                   add_generation_prompt=True)
    inputs = tok(text, return_tensors="pt")
    if seed is not None:
        # Per-call seeding: each sampled completion is reproducible on its
        # own, independent of what was generated before it in the process.
        torch.manual_seed(seed)
    kwargs = dict(max_new_tokens=max_new_tokens, do_sample=do_sample,
                  pad_token_id=tok.eos_token_id)
    if do_sample:
        kwargs["temperature"] = temperature
    with torch.no_grad():
        out = model.generate(**inputs, **kwargs)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:],
                      skip_special_tokens=True)


def generate(prompt: str, max_new_tokens: int = 220) -> str:
    """Greedy-generate a reply to a single user prompt (chat template)."""
    return _generate(prompt, max_new_tokens, do_sample=False)


def sample(prompt: str, temperature: float = 0.7, seed=None,
           max_new_tokens: int = 256) -> str:
    """Sample one completion at ``temperature`` under an explicit seed."""
    return _generate(prompt, max_new_tokens, do_sample=True,
                     temperature=temperature, seed=seed)
