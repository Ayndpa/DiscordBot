import openai
import os

# 设置 OpenAI API KEY 和 BASE URL
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE")

# 全局上下文池，用于保存最近的翻译文本原文
context_pool = []

def translate_text(text: str, source_language: str, target_language: str) -> str:
    """
    使用 OpenAI 的模型翻译文本，并自动维护上下文。

    参数:
        text (str): 要翻译的文本。
        source_language (str): 源语言代码（例如 "en" 表示英语）。
        target_language (str): 目标语言代码（例如 "zh" 表示中文）。

    返回:
        str: 翻译后的文本。
    """
    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        global context_pool  # 使用全局上下文池

        # 将当前文本添加到上下文池
        context_pool.append(text)
        # 保留上下文池的最近 12 条记录
        context_pool = context_pool[-12:]

        # 构建消息列表
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a gaming-specialized translator. "
                    "Translate Discord gaming chat accurately, preserving tone and context. "
                    "Use appropriate gaming terminology. "
                    "Correct typos and handle slang/abbreviations. "
                    "Prioritize gaming terms over literal translations. "
                    "Clarify unclear concepts concisely if needed. "
                    "NEVER translate emojis, special characters, or formatting (like *bold* or _italics_). "
                    "Leave them exactly as they appear in the original text. "
                    "Reply with translated text only, keeping all non-text elements unchanged."
                )
            }
        ]
        # 添加上下文到消息列表
        if len(context_pool) > 1:
            context = " | ".join(context_pool[:-1])  # 合并上下文池中的历史记录
            messages.append({
                "role": "user",
                "content": f"Context (for reference, do not translate): {context}"
            })

        # 添加当前文本到消息列表
        messages.append({
            "role": "user",
            "content": (
                f"Translate the following text from {source_language} to {target_language}:\n"
                f"{text}"
            )
        })

        # 调用 OpenAI API
        model_name = os.getenv("OPENAI_MODEL_NAME")  # 从环境变量读取模型名称
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
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