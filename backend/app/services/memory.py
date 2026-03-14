import os
import uuid
import hashlib
import dashscope
from typing import List
import chromadb
from chromadb.config import Settings
from chromadb.api.types import EmbeddingFunction

# 自定义 DashScope 向量嵌入提取器，供 ChromaDB 使用
class DashScopeEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: List[str]) -> List[List[float]]:
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        # 使用 dashscope 获取 embedding
        resp = dashscope.TextEmbedding.call(
            model=dashscope.TextEmbedding.Models.text_embedding_v2,
            input=input
        )
        if resp.status_code == 200:
            # 返回 embedding 列表
            return [emb["embedding"] for emb in resp.output["embeddings"]]
        else:
            print(f"Embedding failed: {resp}")
            # 如果出错则返回全零张量
            return [[0.0] * 1536 for _ in input]

# 初始化 ChromaDB 本地客户端
CHROMA_DATA_PATH = os.path.join(os.path.dirname(__file__), "../../../data/chroma")
os.makedirs(CHROMA_DATA_PATH, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
embedding_func = DashScopeEmbeddingFunction()

def get_memory_collection(user_id: int, character_id: str):
    """获取指定用户-角色对的专属记忆集合"""
    safe_char_id = hashlib.md5(character_id.encode('utf-8')).hexdigest()
    collection_name = f"memory_{user_id}_{safe_char_id}"
    return chroma_client.get_or_create_collection(
        name=collection_name, 
        embedding_function=embedding_func
    )

def search_memory(user_id: int, character_id: str, query: str, top_k: int = 3) -> str:
    """根据当前对话输入检索最相关的过去记忆"""
    try:
        collection = get_memory_collection(user_id, character_id)
        if collection.count() == 0:
            return ""
        
        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count())
        )
        
        memories = results["documents"][0]
        if not memories:
            return ""
        
        # 拼接成上下文
        context = "\n".join([f"- {m}" for m in memories])
        return context
    except Exception as e:
        print(f"Search memory error: {e}")
        return ""

def add_memory(user_id: int, character_id: str, memory_text: str):
    """将一条新的总结好的记忆文本保存进向量库"""
    if not memory_text.strip():
        return
    try:
        collection = get_memory_collection(user_id, character_id)
        
        # 为了避免完全一样的内容重复存入，可先做简单的去重检索
        # 简单起见，这里直接生成唯一id加入
        doc_id = str(uuid.uuid4())
        collection.add(
            documents=[memory_text],
            ids=[doc_id]
        )
    except Exception as e:
        print(f"Add memory error: {e}")

def extract_and_save_memory(user_id: int, character_id: str, last_user_msg: str, last_ai_reply: str):
    """
    通过模型提炼这段对话中有价值的内容（例如喜好、事件、称呼约定等）并保存
    如果只是一般性聊天，提取为空
    """
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        return
    import dashscope
    dashscope.api_key = api_key
    
    prompt = f"""
请提取以下一轮对话中，用户向 AI 透露的重要信息、角色设定、事情进展或情感倾向，将其总结成一句话的“记忆”。
如果这只是闲聊，请直接回复“无”，不要编造记忆。
必须以第三人称客观陈述（例如：“玩家今天吃了一顿火锅”、“玩家希望我以后叫他哥哥”）。

用户说：{last_user_msg}
AI说：{last_ai_reply}
"""
    try:
        resp = dashscope.Generation.call(
            model=os.getenv("LLM_MODEL", "qwen-plus"),
            messages=[{"role": "user", "content": prompt}],
            result_format="message",
        )
        if resp.status_code == 200:
            content = resp.output["choices"][0]["message"]["content"].strip()
            # 若判定的结果不是“无”，则添加进长期记忆
            if content and content != "无" and "无" not in content and len(content) > 2:
                add_memory(user_id, character_id, content)
                print(f"[记忆触发已经保存] {content}")
    except Exception as e:
        print(f"Extract memory error: {e}")
