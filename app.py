import asyncio
import discord
from discord.ext import commands
from llm import translate_text
import os

# 设置Intents，包括消息内容权限
intents = discord.Intents.default()
intents.message_content = True  # 启用消息内容权限

# 创建Bot实例
bot = discord.Client(intents=intents)

# 定义频道名与目标语言的映射
CHANNEL_LANGUAGE_MAP = {
    "中文": "zh",
    "日本語": "ja",
    "한국인": "ko"
}

# 翻译并发送消息的独立函数
async def process_translation(message, source_language, guild, channel_name, target_language):
    if channel_name != message.channel.name:
        target_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if target_channel:
            # 如果消息包含文本，进行翻译
            if message.content:
                translated_message = translate_text(message.content, source_language, target_language)
                if translated_message:
                    embed = discord.Embed(
                        description=translated_message,
                        color=discord.Color.blue()
                    )
                    embed.set_author(name=f"{message.author.display_name} said:", icon_url=message.author.avatar.url if message.author.avatar else None)
                    await target_channel.send(embed=embed)
            
            # 如果消息包含图片，转发图片
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.url.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'webp')):
                        await target_channel.send(content=f"{message.author.display_name} shared an image:", file=await attachment.to_file())
            
            # 如果消息包含贴纸，转发贴纸
            if message.stickers:
                for sticker in message.stickers:
                    await target_channel.send(content=f"{message.author.display_name} shared a sticker: {sticker.url}")

# Bot启动时的事件
@bot.event
async def on_ready():
    print(f'{bot.user} 已成功登录!')

# 当收到消息时的事件
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    source_channel = message.channel
    guild = message.guild

    if source_channel.name in CHANNEL_LANGUAGE_MAP:
        source_language = CHANNEL_LANGUAGE_MAP[source_channel.name]
        tasks = [
            asyncio.create_task(process_translation(message, source_language, guild, channel_name, target_language))
            for channel_name, target_language in CHANNEL_LANGUAGE_MAP.items()
        ]
        await asyncio.gather(*tasks)

# 运行Bot
bot.run(os.getenv('DISCORD_BOT_TOKEN'))