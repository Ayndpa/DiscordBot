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

# 辅助函数：处理引用消息的翻译
async def handle_referenced_message(message, guild, source_language, target_language, target_channel):
    if message.reference and message.reference.resolved:
        referenced_message = message.reference.resolved
        if referenced_message.content:  # 如果引用的是文本消息
            translated_reference = translate_text(referenced_message.content, source_language, target_language)
            if translated_reference:
                embed = discord.Embed(
                    description=f"**Referenced message:** {translated_reference}",
                    color=discord.Color.green()
                )
                embed.set_author(name=f"{referenced_message.author.display_name} said:", icon_url=referenced_message.author.avatar.url if referenced_message.author.avatar else None)
                await target_channel.send(embed=embed)
        elif referenced_message.attachments:  # 如果引用的是附件
            for attachment in referenced_message.attachments:
                embed = discord.Embed(color=discord.Color.green())
                embed.set_image(url=attachment.url)
                embed.set_author(name=f"{referenced_message.author.display_name} shared an image:", icon_url=referenced_message.author.avatar.url if referenced_message.author.avatar else None)
                await target_channel.send(embed=embed)
        elif referenced_message.stickers:  # 如果引用的是贴纸
            for sticker in referenced_message.stickers:
                await target_channel.send(f"{referenced_message.author.display_name} shared a sticker:", stickers=[sticker])

# 翻译并发送消息的独立函数
async def process_translation(message, source_language, guild, channel_name, target_language):
    if channel_name != message.channel.name:
        target_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if target_channel:
            translated_message = translate_text(message.content, source_language, target_language)
            if translated_message:
                embed = discord.Embed(
                    description=translated_message,
                    color=discord.Color.blue()
                )
                embed.set_author(name=f"{message.author.display_name} said:", icon_url=message.author.avatar.url if message.author.avatar else None)
                await target_channel.send(embed=embed)
            # 处理引用消息
            await handle_referenced_message(message, guild, source_language, target_language, target_channel)

# 辅助函数：转发贴纸或图片
async def forward_stickers_and_attachments(message, guild):
    for channel_name in CHANNEL_LANGUAGE_MAP.keys():
        if channel_name != message.channel.name:
            target_channel = discord.utils.get(guild.text_channels, name=channel_name)
            if target_channel:
                # 转发贴纸
                if message.stickers:
                    for sticker in message.stickers:
                        await target_channel.send(f"{message.author.display_name} shared a sticker:", stickers=[sticker])
                # 转发图片
                if message.attachments:
                    for attachment in message.attachments:
                        embed = discord.Embed(color=discord.Color.blue())
                        embed.set_image(url=attachment.url)
                        embed.set_author(name=f"{message.author.display_name} shared an image:", icon_url=message.author.avatar.url if message.author.avatar else None)
                        await target_channel.send(embed=embed)

# 辅助函数：处理普通文本消息
async def handle_text_message(message, guild):
    if not message.content.strip():  # 如果消息内容为空，跳过处理
        return

    source_channel = message.channel
    if source_channel.name in CHANNEL_LANGUAGE_MAP:
        source_language = CHANNEL_LANGUAGE_MAP[source_channel.name]
        tasks = [
            asyncio.create_task(process_translation(message, source_language, guild, channel_name, target_language))
            for channel_name, target_language in CHANNEL_LANGUAGE_MAP.items()
        ]
        await asyncio.gather(*tasks)

# Bot启动时的事件
@bot.event
async def on_ready():
    print(f'{bot.user} 已成功登录!')

# 当收到消息时的事件
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    guild = message.guild

    # 如果消息包含贴纸或图片，直接转发到目标频道
    if message.stickers or message.attachments:
        await forward_stickers_and_attachments(message, guild)
        return

    # 如果是普通文本消息，执行翻译逻辑
    await handle_text_message(message, guild)

# 运行Bot
bot.run(os.getenv('DISCORD_BOT_TOKEN'))