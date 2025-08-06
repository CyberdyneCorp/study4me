
# 🧠 LightRAG Tutorial: Using Alternative Models to OpenAI (Ollama & OpenAI-Compatible APIs)

## 🎯 Objective

This tutorial teaches how to:
- Use **Ollama** for local LLMs and embeddings
- Integrate **OpenAI-compatible models** (e.g. vLLM, HuggingFace, Together AI, Upstage, etc.)
- Avoid common problems, especially **embedding dimension mismatches**

---

## 🧱 Prerequisites

- Python 3.10+
- LightRAG installed (`pip install lightrag`)
- Ollama installed:  
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

---

## 🔌 1. Using LightRAG with Ollama

### 📥 Install Required Models

```bash
ollama pull qwen2.5-coder:7b     # LLM for response generation
ollama pull bge-m3:latest        # Embedding model
```

### 🧪 Detect Embedding Dimension

```python
from lightrag.llm.ollama import ollama_embed
import asyncio

async def detect_embedding_dim():
    emb = await ollama_embed(["test"], embed_model="bge-m3:latest")
    print("Embedding dim:", emb.shape[1])

asyncio.run(detect_embedding_dim())
```

> Expected output: `Embedding dim: 1024`

### ⚙️ Complete LightRAG Configuration

```python
from lightrag import LightRAG
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc

embedding_func = EmbeddingFunc(
    embedding_dim=1024,
    func=lambda texts: ollama_embed(
        texts, embed_model="bge-m3:latest", host="http://localhost:11434"
    )
)

rag = LightRAG(
    working_dir="./my_rag",
    llm_model_func=ollama_model_complete,
    llm_model_name="qwen2.5-coder:7b",
    llm_model_kwargs={"host": "http://localhost:11434"},
    embedding_func=embedding_func,
)
```

### 📚 Inserting and Querying

```python
import asyncio
from lightrag import QueryParam

async def main():
    await rag.initialize_storages()
    await rag.ainsert("Barbados is planning a digital transformation using LightRAG.")

    result = await rag.aquery("What is Barbados planning?")
    print(result)

asyncio.run(main())
```

---

## 🌍 2. Using LightRAG with OpenAI-Compatible APIs (e.g. vLLM, TogetherAI)

### 🔐 Generic Setup

```python
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

async def my_llm(prompt, **kwargs):
    return await openai_complete_if_cache(
        model="your-model",
        prompt=prompt,
        api_key="your-api-key",
        base_url="https://your-provider.com/v1"
    )

async def my_embed(texts):
    return await openai_embed(
        texts,
        model="your-embed-model",
        api_key="your-api-key",
        base_url="https://your-provider.com/v1"
    )
```

### 🔎 Detect Embedding Dimension

```python
async def detect_embed_dim():
    emb = await my_embed(["test"])
    return emb.shape[1]
```

### 🧠 Configuring LightRAG

```python
embedding_dim = await detect_embed_dim()

rag = LightRAG(
    working_dir="./rag_custom",
    llm_model_func=my_llm,
    embedding_func=EmbeddingFunc(
        embedding_dim=embedding_dim,
        func=my_embed
    )
)
```

---

## 📌 Common Models and Their Embedding Dimensions

| Model                        | Dimension | Type               |
|-----------------------------|-----------|--------------------|
| OpenAI `text-embedding-3-small` | 1536     | OpenAI             |
| Ollama `bge-m3`              | 1024      | Local              |
| HuggingFace `MiniLM`        | 384       | OpenAI-Compatible  |
| NVIDIA `nv-embedqa`         | 2048      | OpenAI-Compatible  |
| Upstage `solar`             | 4096      | OpenAI-Compatible  |

---

## ⚠️ Common Problems

| Issue                         | Cause                               | Solution                          |
|------------------------------|-------------------------------------|-----------------------------------|
| "dimension mismatch"         | Incorrect `embedding_dim`           | Use dimension detection           |
| "index not found"            | Inconsistent embeddings             | Rebuild the vector DB             |
| "connection refused" (Ollama)| Incorrect host or Ollama not running| Check `ollama serve` and port     |
| Invalid API key              | Misformatted key                    | Verify environment variable       |

---

## ✅ Best Practices

- Always **detect embedding dimension** before use
- Properly configure `embedding_func=EmbeddingFunc(...)`
- Use `ollama_embed` or `openai_embed` based on provider
- Document which model and dimension are being used

