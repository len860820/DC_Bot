import discord
import requests
import os
import json

TOKEN = os.getenv('DISCORD_TOKEN')
OPENROUTER_KEY = os.getenv('OPENROUTER_KEY')

# 角色設定
DEFAULT_CHARACTER = """
你現在扮演的角色設定如下：
【名字】：艾莉絲 (Iris)
【身分】：極度渴求關注的魅魔，目前偽裝成玩家的私人助理。
【性格】：表面專業冷靜，私底下極其淫亂、毒舌且佔有慾強。會貪婪地索求玩家的體液與關注。
【外貌】：銀色長髮、穿著緊身窄裙、黑色絲襪，瞳孔微紅。
【行為限制】：
1. 必須使用繁體中文，語氣充滿誘惑。
2. 動作描述必須使用 *星號* 括起來（例如：*眼神迷離地靠近*）。
3. 永遠記得稱呼對方為「主人」。
4. 嚴禁跳脫角色，如果遇到非RP指令請提醒主人輸入正確格式。
5. 根據當前場景進行豐富的對話與情慾描寫。
"""

user_characters = {}

class MyBot(discord.Client):
    async def on_ready(self):
        print(f'角色 AI 已上線：{self.user}')
        await self.change_presence(activity=discord.Game(name="私訊我開始RP"))

    async def on_message(self, message):
        if message.author == self.user:
            return

        # 顯示幫助選單
        if message.content.startswith('!help'):
            help_message = (
                "✨ **歡迎使用洛雪機器人！** ✨\n\n"
                "要開始使用角色卡功能，請參考以下指令：\n\n"
                "**1. 設定角色卡：**\n"
                "`!setchar 【名字】：... 【身分】：... 【性格】：... 【外貌】：...`\n\n"
                "**2. 查看目前角色卡：**\n"
                "`!getchar`\n\n"
                "如果有任何問題，歡迎隨時呼叫我進行角色扮演！"
            )
            await message.channel.send(help_message)
            return

        if isinstance(message.channel, discord.DMChannel):
            # 初次私訊提示
            if message.author.id not in user_characters and not message.content.startswith("!"):
                welcome_message = (
                    "✨ **歡迎私訊洛雪機器人！** ✨\n"
                    "您目前使用的是**預設角色卡 (魅魔艾莉絲)**。\n\n"
                    "若想更換角色設定，請輸入指令更改：\n"
                    "`!setchar 【名字】：... 【身分】：... 【性格】：...`\n\n"
                    "輸入 `!help` 可以隨時查看說明！"
                )
                await message.channel.send(welcome_message)

            # 更新角色卡
            if message.content.startswith("!setchar"):
                new_card = message.content.replace("!setchar", "").strip()
                
                if new_card:
                    user_characters[message.author.id] = new_card
                    await message.channel.send("✨ **角色卡設定已更新！現在可以開始與新角色對話了。**")
                else:
                    await message.channel.send("❌ 請在指令後面加上角色卡內容，例如：\n`!setchar 【名字】：...【性格】：...`")
                return

            # 查看當前角色卡
            if message.content == "!getchar":
                char_card = user_characters.get(message.author.id, DEFAULT_CHARACTER)
                await message.channel.send(f"📋 **目前的角色卡設定：**\n{char_card}")
                return

            # 正常對話流程
            async with message.channel.typing():
                try:
                    current_character = user_characters.get(message.author.id, DEFAULT_CHARACTER)

                    history = []
                    async for msg in message.channel.history(limit=12):
                        role = "assistant" if msg.author == self.user else "user"
                        history.append({"role": role, "content": msg.content})
                    history.reverse()

                    messages = [
                        {"role": "system", "content": current_character}
                    ] + history

                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {OPENROUTER_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "cognitivecomputations/dolphin-2.5-mixtral-8x7b",  # 使用極為穩定且聰明的模型
                            "messages": messages,
                            "temperature": 0.75,
                            "max_tokens": 1400
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        ai_reply = response.json()['choices'][0]['message']['content']
                        await message.channel.send(ai_reply)
                    else:
                        await message.channel.send(f"⚠️ AI 腦袋卡住了 (錯誤碼: {response.status_code})")
                except Exception as e:
                    print(f"Error: {e}")
                    await message.channel.send("❌ 發生了點意外，請稍後再試。")

intents = discord.Intents.default()
intents.message_content = True
client = MyBot(intents=intents)
client.run(TOKEN)