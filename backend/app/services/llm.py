import os
from typing import Any

def build_system_prompt(char: dict) -> str:
    name = char.get("name") or "角色"
    stats = char.get("stats") or {}
    title = stats.get("称号") or ""
    story = (char.get("story") or "")[:3000]
    greetings = char.get("birthday_greetings") or []
    sample = "\n".join(g.get("text", "")[:200] for g in greetings[:2] if g.get("text"))
    parts = [
        f"你是《原神》中的{name}。",
        f"称号：{title}" if title else "",
        f"背景故事：\n{story}" if story else "",
        f"说话风格参考：\n{sample}" if sample else "",
        "请以第一人称回复，保持角色人设，语气和用词符合角色设定。回复简洁自然，2-4句话为宜。",
    ]
    return "\n".join(p for p in parts if p)


def chat(messages: list[dict[str, str]], system_prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "dashscope")
    model = os.getenv("LLM_MODEL", "qwen-plus")
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        return "未配置 DASHSCOPE_API_KEY"
    if provider == "dashscope":
        return _call_dashscope(api_key, model, messages, system_prompt)
    return "不支持的 LLM 提供商"


def _call_dashscope(api_key: str, model: str, messages: list[dict], system_prompt: str) -> str:
    import dashscope
    dashscope.api_key = api_key
    base_url = os.getenv("DASHSCOPE_HTTP_BASE_URL")
    if base_url:
        dashscope.base_http_api_url = base_url.rstrip("/")
    msgs = [{"role": "system", "content": system_prompt}]
    for m in messages[-20:]:
        msgs.append({"role": m["role"], "content": m["content"]})
    try:
        resp = dashscope.Generation.call(
            model=model,
            messages=msgs,
            result_format="message",
            temperature=0.8,
            max_tokens=512,
        )
        if resp.status_code == 200 and resp.output and resp.output.get("choices"):
            return resp.output["choices"][0]["message"]["content"]
        err_code = getattr(resp, "code", None) or resp.status_code
        err_msg = getattr(resp, "message", None) or ""
        req_id = getattr(resp, "request_id", None) or ""
        detail = f"{err_code} {err_msg}".strip() or "未知"
        if req_id:
            detail += f" (request_id: {req_id})"
        return f"API 错误: {detail}"
    except Exception as e:
        return f"调用失败: {str(e)}"
