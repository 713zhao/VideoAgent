from __future__ import annotations
from typing import Dict, Any
import json

from .config import SummarizerCfg


def translate_text(cfg: SummarizerCfg, text: str, target_lang: str = "zh") -> str:
    """
    Translate a plain text string to the target language using the configured summarizer backend.
    Falls back to returning the original text when translation is not available.
    """
    if not text:
        return ""

    # Simple local fallback: if using local_dummy, just return the original text
    if cfg.backend == "local_dummy":
        return text

    # Use Gemini backend if configured
    if cfg.backend == "gemini":
        try:
            from google import genai
            from google.genai import types
        except Exception as e:
            print(f"⚠️ Gemini translate client unavailable: {e}")
            return text

        gemini_cfg = cfg.gemini
        client = genai.Client(api_key=gemini_cfg.api_key())

        prompt = f"Translate the following text to {target_lang} while preserving meaning and formatting.\n\nTEXT:\n" + text

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=gemini_cfg.max_tokens,
            response_mime_type="text/plain"
        )

        try:
            parts = []
            for chunk in client.models.generate_content_stream(
                model=gemini_cfg.model,
                contents=contents,
                config=generate_content_config
            ):
                if chunk.text:
                    parts.append(chunk.text)
            return "".join(parts).strip()
        except Exception as e:
            print(f"⚠️ Gemini translation failed: {e}")
            return text

    # OpenAI-compatible backend
    if cfg.backend == "openai_compatible":
        try:
            import requests
            oai = cfg.openai_compatible
            base = oai.base_url.rstrip("/")
            url = f"{base}/chat/completions"

            system = f"You are a translation assistant. Translate user content to {target_lang} preserving meaning and formatting."
            payload = {
                "model": oai.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.1,
                "max_tokens": oai.max_tokens
            }
            headers = {"Authorization": f"Bearer {oai.api_key()}", "Content-Type": "application/json"}
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip()
        except Exception as e:
            print(f"⚠️ OpenAI-compatible translation failed: {e}")
            return text

    return text


def translate_bundle(cfg: SummarizerCfg, bundle: Dict[str, Any], target_lang: str = "zh") -> Dict[str, Any]:
    """
    Translate key fields of the summarization bundle: `narration` and each topic `summary`.
    Returns a new bundle dict with translated fields.
    """
    if not bundle:
        return bundle

    # Helper: detect if text contains CJK (Chinese) characters
    def is_chinese_text(s: str) -> bool:
        if not s:
            return False
        for ch in s:
            if "\u4e00" <= ch <= "\u9fff":
                return True
        return False

    # Attempt a single batched translation call for the English parts of the
    # bundle when using an LLM backend to reduce the number of API requests
    # and avoid quota exhaustion. If batching fails, fall back to per-field calls.
    if not bundle:
        return bundle

    # Build a compact English payload to send for translation
    try:
        # Prepare payload with ONLY English pieces (skip already-Chinese items)
        topics = bundle.get("topics", [])
        captions = bundle.get("captions", [])

        payload_topics = []
        topic_index_map = []  # maps payload index -> original topic index
        for i, t in enumerate(topics):
            title = t.get("title", "")
            summary = t.get("summary", "")
            # If summary/title already contains Chinese, skip translation for this topic
            if is_chinese_text(summary) or is_chinese_text(title):
                topic_index_map.append(None)
                continue
            payload_topics.append({"title": title, "summary": summary})
            topic_index_map.append(len(payload_topics) - 1)

        # Build an "english narration" from only the English topics, in order
        english_narration_parts = []
        for i, t in enumerate(topics):
            if topic_index_map[i] is not None:
                title = t.get("title", "")
                summary = t.get("summary", "")
                english_narration_parts.append(f"{i+1}. {title}: {summary}")

        payload_captions = []
        caption_index_map = []
        for i, c in enumerate(captions):
            text = c.get("text", "")
            if is_chinese_text(text):
                caption_index_map.append(None)
                continue
            payload_captions.append(text)
            caption_index_map.append(len(payload_captions) - 1)

        # If there's nothing English to translate, return original bundle
        if not english_narration_parts and not payload_topics and not payload_captions:
            return bundle

        payload = {
            "narration": "\n\n".join(english_narration_parts),
            "topics": payload_topics,
            "captions": payload_captions,
        }

        if cfg.backend == "local_dummy":
            return bundle

        # Gemini backend: use streaming and expect a JSON response
        if cfg.backend == "gemini":
            try:
                from google import genai
                from google.genai import types
            except Exception as e:
                print(f"⚠️ Gemini translate client unavailable: {e}")
                # Fallback to per-field translation
                raise

            gemini_cfg = cfg.gemini
            client = genai.Client(api_key=gemini_cfg.api_key())

            system_prompt = f"You are a translation assistant. Translate the provided JSON object into {target_lang}, preserving meaning and formatting. Return valid JSON with the same structure: {{'narration': string, 'topics': [{{title,summary}}], 'captions':[string]}}."
            user_prompt = "INPUT_JSON:\n" + json.dumps(payload, ensure_ascii=False)

            contents = [
                types.Content(role="user", parts=[types.Part.from_text(text=system_prompt + "\n\n" + user_prompt)])
            ]

            generate_content_config = types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=gemini_cfg.max_tokens,
                response_mime_type="application/json"
            )

            print("🔄 Requesting batched translation from Gemini...")
            content_parts = []
            try:
                for chunk in client.models.generate_content_stream(
                    model=gemini_cfg.model,
                    contents=contents,
                    config=generate_content_config
                ):
                    if chunk.text:
                        content_parts.append(chunk.text)

                content = "".join(content_parts).strip()
                # Strip code fences if present
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                translated_obj = json.loads(content)
                # Map translated fields back into bundle structure
                out = dict(bundle)
                out["narration"] = translated_obj.get("narration", out.get("narration", ""))
                # topics: use topic_index_map to map translated entries back to originals
                out_topics = []
                translated_topics = translated_obj.get("topics", [])
                for i, t in enumerate(bundle.get("topics", [])):
                    t_copy = dict(t)
                    mapped = topic_index_map[i] if i < len(topic_index_map) else None
                    if mapped is not None and mapped < len(translated_topics):
                        tr = translated_topics[mapped]
                        t_copy["summary"] = tr.get("summary", t_copy.get("summary", ""))
                        t_copy["title"] = tr.get("title", t_copy.get("title", ""))
                    out_topics.append(t_copy)
                out["topics"] = out_topics
                # captions: map back using caption_index_map
                out_caps = []
                translated_caps = translated_obj.get("captions", [])
                for i, c in enumerate(bundle.get("captions", [])):
                    text = c.get("text", "")
                    mapped_c = caption_index_map[i] if i < len(caption_index_map) else None
                    if mapped_c is not None and mapped_c < len(translated_caps):
                        text = translated_caps[mapped_c]
                    c_copy = dict(c)
                    c_copy["text"] = text
                    out_caps.append(c_copy)
                out["captions"] = out_caps

                return out
            except Exception as e:
                print(f"⚠️ Batched Gemini translation failed: {e}")
                # Fall through to per-field translation below

        # OpenAI-compatible backend: send one chat completion request and parse JSON
        if cfg.backend == "openai_compatible":
            try:
                import requests
                oai = cfg.openai_compatible
                base = oai.base_url.rstrip("/")
                url = f"{base}/chat/completions"

                system = f"You are a translation assistant. Translate the provided JSON into {target_lang} preserving meaning and formatting. Return only valid JSON with keys: narration, topics (list of {{title,summary}}), captions (list of strings)."
                user = "INPUT_JSON:\n" + json.dumps(payload, ensure_ascii=False)
                payload_req = {
                    "model": oai.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    "temperature": 0.1,
                    "max_tokens": oai.max_tokens
                }
                headers = {"Authorization": f"Bearer {oai.api_key()}", "Content-Type": "application/json"}
                r = requests.post(url, headers=headers, json=payload_req, timeout=120)
                r.raise_for_status()
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                # Strip fences
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                translated_obj = json.loads(content)
                # Map back into bundle (same as Gemini mapping)
                out = dict(bundle)
                out["narration"] = translated_obj.get("narration", out.get("narration", ""))
                translated_topics = translated_obj.get("topics", [])
                out_topics = []
                for i, t in enumerate(bundle.get("topics", [])):
                    t_copy = dict(t)
                    mapped = topic_index_map[i] if i < len(topic_index_map) else None
                    if mapped is not None and mapped < len(translated_topics):
                        tr = translated_topics[mapped]
                        t_copy["summary"] = tr.get("summary", t_copy.get("summary", ""))
                        t_copy["title"] = tr.get("title", t_copy.get("title", ""))
                    out_topics.append(t_copy)
                out["topics"] = out_topics
                translated_caps = translated_obj.get("captions", [])
                out_caps = []
                for i, c in enumerate(bundle.get("captions", [])):
                    text = c.get("text", "")
                    mapped_c = caption_index_map[i] if i < len(caption_index_map) else None
                    if mapped_c is not None and mapped_c < len(translated_caps):
                        text = translated_caps[mapped_c]
                    c_copy = dict(c)
                    c_copy["text"] = text
                    out_caps.append(c_copy)
                out["captions"] = out_caps

                return out
            except Exception as e:
                print(f"⚠️ Batched OpenAI-compatible translation failed: {e}")
                # Fall through to per-field translation

    except Exception:
        # If any unexpected error happens, fall back to per-field translation
        pass

    # Fallback: translate field-by-field (original behavior)
    translated = dict(bundle)

    # Translate narration
    narration = bundle.get("narration", "")
    translated_narration = translate_text(cfg, narration, target_lang)
    translated["narration"] = translated_narration

    # Translate topics summaries and titles if present
    out_topics = []
    for t in bundle.get("topics", []):
        t_copy = dict(t)
        summary = t.get("summary", "")
        title = t.get("title", "")
        # Skip translating topics that already contain Chinese characters
        if summary and not is_chinese_text(summary):
            t_copy["summary"] = translate_text(cfg, summary, target_lang)
        else:
            t_copy["summary"] = summary
        if title and not is_chinese_text(title):
            t_copy["title"] = translate_text(cfg, title, target_lang)
        else:
            t_copy["title"] = title
        out_topics.append(t_copy)
    translated["topics"] = out_topics

    # Translate captions text
    caps = []
    for c in bundle.get("captions", []):
        c_copy = dict(c)
        text = c.get("text", "")
        if text and not is_chinese_text(text):
            c_copy["text"] = translate_text(cfg, text, target_lang)
        else:
            c_copy["text"] = text
        caps.append(c_copy)
    translated["captions"] = caps

    return translated
