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

# 辅助函数：生成引用消息链接
def generate_message_link(referenced_message):
    return f"https://discord.com/channels/{referenced_message.guild.id}/{referenced_message.channel.id}/{referenced_message.id}"

# 辅助函数：处理引用消息内容
async def process_referenced_message(referenced_message, source_language, target_language):
    original_message_link = generate_message_link(referenced_message)
    author_name = referenced_message.author.display_name

    if referenced_message.content:
        translated_content = translate_text(referenced_message.content, source_language, target_language)
        return f"**{author_name}** said:\n{translated_content}\n[Jump to original message]({original_message_link})"
    elif referenced_message.stickers:
        return f"**{author_name}** referenced a sticker. [Jump to original message]({original_message_link})"
    elif referenced_message.attachments:
        return f"**{author_name}** referenced an attachment: {referenced_message.attachments[0].url}\n[Jump to original message]({original_message_link})"
    
    if isinstance(referenced_message.embeds, list) and referenced_message.embeds:
        embed = referenced_message.embeds[0]
        embed_data = embed.to_dict()
        if 'fields' in embed_data:
            for field in embed_data['fields']:
                if field['name'] == 'Message' and 'value' in field:
                    translated_value = translate_text(field['value'], source_language, target_language)
                    author_name = embed_data['author']['name'] if 'author' in embed_data and 'name' in embed_data['author'] else "Unknown"
                    return f"**{author_name}**\n{translated_value}\n[Jump to original message]({original_message_link})"

    return None

# 翻译并发送消息的独立函数
async def process_translation(message, source_language, guild, channel_name, target_language):
    if channel_name == message.channel.name:
        return

    target_channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not target_channel:
        return

    translated_message = translate_text(message.content, source_language, target_language)
    translated_reference = None

    # 如果有引用消息，处理引用消息的翻译或链接
    if message.reference and message.reference.resolved:
        translated_reference = await process_referenced_message(message.reference.resolved, source_language, target_language)

    if translated_message or translated_reference:
        embed = discord.Embed(color=discord.Color.blue())

        # 添加引用消息的翻译或链接
        if translated_reference:
            embed.add_field(name="Referenced message", value=translated_reference, inline=False)

        # 添加原消息的翻译
        if translated_message:
            embed.add_field(name="Message", value=translated_message, inline=False)

        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url if message.author.avatar else None)
        
        await target_channel.send(embed=embed)

# 辅助函数：转发贴纸或图片
async def forward_stickers_and_attachments(message, guild):
    for channel_name, _ in CHANNEL_LANGUAGE_MAP.items():
        if channel_name == message.channel.name:
            continue

        target_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not target_channel:
            continue

        # 转发贴纸
        if message.stickers:
            for sticker in message.stickers:
                await target_channel.send(f"{message.author.display_name} shared a sticker:", stickers=[sticker])

        # 转发图片
        if message.attachments:
            for attachment in message.attachments:
                embed = discord.Embed(color=discord.Color.blue())
                embed.set_image(url=attachment.url)
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url if message.author.avatar else None)
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