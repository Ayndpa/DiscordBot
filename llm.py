import openai
import os

# 设置 OpenAI API KEY 和 BASE URL
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE")

# 全局变量，用于存储聊天消息
chat_messages = [
    {
        "role": "system",
        "content": (
            "You are an expert translator. "
            "Translate user input accurately from the source language to the target language. "
            "Preserve meaning, tone, and context. "
            "If context is provided, use it to improve translation quality. "
            "Only reply with the translated text, without explanations."
        )
    }
]

def translate_text(text: str, source_language: str, target_language: str) -> str:
    """
    使用 OpenAI 的模型翻译文本。

    参数:
        text (str): 要翻译的文本。
        source_language (str): 源语言代码（例如 "en" 表示英语）。
        target_language (str): 目标语言代码（例如 "zh" 表示中文）。

    返回:
        str: 翻译后的文本。
    """
    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        global chat_messages  # 使用全局消息列表
        chat_messages.append({
            "role": "user",
            "content": (
                f"Translate the following text from {source_language} to {target_language}:\n"
                f"{text}"
            )
        })
        
        # 保留 System 消息和最近 20 条用户消息
        chat_messages = chat_messages[:1] + [
            msg for msg in chat_messages[1:] if msg["role"] == "user"
        ][-20:]

        response = client.chat.completions.create(
            model="qwen-plus-latest",
            messages=chat_messages,
            max_tokens=1000,
            temperature=0.3
        )
        # 提取翻译结果
        translated_text = response.choices[0].message.content.strip()
        
        return translated_text
    except openai.APIError as e:
        print(f"API 错误: {e}")
    except openai.APIConnectionError as e:
        print(f"连接错误: {e}")
    except openai.RateLimitError as e:
        print(f"超出速率限制: {e}")
    except Exception as e:
        print(f"未知错误: {e}")
    return ""