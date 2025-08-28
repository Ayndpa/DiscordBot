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
                    "You are an expert translator. "
                    "Translate user input accurately from the source language to the target language. "
                    "Preserve meaning, tone, and context. "
                    "The input text is from a Discord chat, so it may contain informal language, abbreviations, slang, and typos. Handle any typos by correcting them where appropriate to ensure accurate translation. "
                    "If context is provided, use it to improve translation quality. "
                    "If you encounter complex concepts or meanings that are unclear or not understood, provide a brief explanation along with the translation to clarify, but keep it concise and integrated. "
                    "Reply with the translated text, including any necessary explanations without additional commentary."
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
        response = client.chat.completions.create(
            model="qwen-plus-latest",
            messages=messages,
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