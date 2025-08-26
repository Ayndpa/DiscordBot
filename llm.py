import openai
import os

# 设置 OpenAI API KEY 和 BASE URL
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE")

def translate_text(text: str, source_language: str, target_language: str, context: str = "") -> str:
    """
    使用 OpenAI 的模型翻译文本，并支持上下文。

    参数:
        text (str): 要翻译的文本。
        source_language (str): 源语言代码（例如 "en" 表示英语）。
        target_language (str): 目标语言代码（例如 "zh" 表示中文）。
        context (str): 上下文信息，可选。

    返回:
        str: 翻译后的文本。
    """
    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        messages = [
            {"role": "system", "content": "You are a helpful translation assistant."}
        ]
        if context:
            messages.append({"role": "user", "content": f"Context(don't translate, just for understanding): {context}"})
        messages.append({"role": "user", "content": f"Translate the following text from {source_language} to {target_language}:\n\n{text}"})
        
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
    

# 示例用法
original_text = "Hello, how are you?"
translated = translate_text(original_text, "en", "zh")
print(f"原文: {original_text}")
print(f"译文: {translated}")