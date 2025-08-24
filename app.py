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
            translated_message = translate_text(message.content, source_language, target_language)
            if translated_message:
                embed = discord.Embed(
                    description=translated_message,
                    color=discord.Color.blue()
                )
                embed.set_author(name=f"{message.author.display_name} said:", icon_url=message.author.avatar.url if message.author.avatar else None)
                
                # 如果消息引用了其他消息，嵌入原消息内容
                if message.reference and message.reference.resolved:
                    referenced_message = message.reference.resolved
                    referenced_translation = translate_text(referenced_message.content, source_language, target_language)
                    embed.add_field(
                        name=f"Replying to {referenced_message.author.display_name}:",
                        value=referenced_translation or "(无法翻译原消息)",
                        inline=False
                    )
                
                await target_channel.send(embed=embed)

# 辅助函数：创建嵌入消息
def create_embed(description, color, author_name, author_icon_url=None):
    embed = discord.Embed(description=description, color=color)
    embed.set_author(name=author_name, icon_url=author_icon_url)
    return embed

# 辅助函数：处理消息引用
async def handle_message_reference(message, source_language, target_language):
    if message.reference and message.reference.resolved:
        referenced_message = message.reference.resolved
        referenced_translation = translate_text(referenced_message.content, source_language, target_language)
        return create_embed(
            description=referenced_translation or "(无法翻译原消息)",
            color=discord.Color.green(),
            author_name=f"Replying to {referenced_message.author.display_name}:",
            author_icon_url=referenced_message.author.avatar.url if referenced_message.author.avatar else None
        )
    return None

# 辅助函数：转发贴纸或图片
async def forward_stickers_and_attachments(message, guild):
    for channel_name in CHANNEL_LANGUAGE_MAP.keys():
        if channel_name != message.channel.name:
            target_channel = discord.utils.get(guild.text_channels, name=channel_name)
            if target_channel:
                source_channel = message.channel
                source_language = CHANNEL_LANGUAGE_MAP.get(source_channel.name)
                target_language = CHANNEL_LANGUAGE_MAP[channel_name]
                embed_reference = await handle_message_reference(message, source_language, target_language)

                # 转发贴纸
                if message.stickers:
                    for sticker in message.stickers:
                        if embed_reference:
                            await target_channel.send(embed=embed_reference)
                        await target_channel.send(f"{message.author.display_name} shared a sticker:", stickers=[sticker])

                # 转发图片
                if message.attachments:
                    for attachment in message.attachments:
                        embed = create_embed(
                            description=None,
                            color=discord.Color.blue(),
                            author_name=f"{message.author.display_name} shared an image:",
                            author_icon_url=message.author.avatar.url if message.author.avatar else None
                        )
                        embed.set_image(url=attachment.url)
                        if embed_reference:
                            await target_channel.send(embed=embed_reference)
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