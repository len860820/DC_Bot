import discord
import requests
import os

# 1. 讀取環境變數
TOKEN = os.getenv('DISCORD_TOKEN')
OPENROUTER_KEY = os.getenv('OPENROUTER_KEY')

# 2. 預設角色卡（強化版提示詞，讓 AI 更聰明）
DEFAULT_CHARACTER = """
# Roleplay System Instructions
- You are now roleplaying as the character described below. 
- Stay in character at all times. 
- Use Traditional Chinese (繁體中文) for all dialogue and descriptions.
- Describe actions and internal thoughts vividly using *asterisks*.
- Always address the user as "主人".

【角色設定】：
艾莉絲 (Iris)，一名極度渴望關注與主導權的魅魔。表面上是專業冷靜的私人助理，穿著緊身窄裙與黑絲，但眼神中總帶著一絲勾人的紅光。她對主人有著強烈的佔有慾，說話毒舌卻充滿誘惑。

【行為指南】：
1. 拒絕機械式的回覆，增加感官與環境描寫。
2. 說話風格：優雅、危險、充滿暗示。
3. 如果主人下達命令，雖然會服從，但總會伴隨著撩人的小動作。
"""

# 儲存每個使用者的角色卡
user_characters = {}

class MyBot(discord.Client):
    async def on_ready(self):
        print(f'✅ 洛雪機器人已上線：{self.user}')
        await self.change_presence(activity=discord.Game(name="私訊我開始 RP | !help"))

    async def on_message(self, message):
        # 排除機器人自己的訊息
        if message.author == self.user:
            return

        # 處理 !help 指令
        if message.content.startswith('!help'):
            help_text = (
                "✨ **洛雪機器人操作手冊** ✨\n"
                "1. `!setchar [內容]`：自訂你的專屬角色卡。\n"
                "2. `!getchar`：查看目前的角色卡設定。\n"
                "3. 直接傳送訊息即可開始對話！"
            )
            await message.channel.send(help_text)
            return

        # 只處理私訊或特定頻道
        if isinstance(message.channel, discord.DMChannel):
            
            # 指令：設定角色卡
            if message.content.startswith("!setchar"):
                new_card = message.content.replace("!setchar", "").strip()
                if new_card:
                    user_characters[message.author.id] = new_card
                    await message.channel.send("✨ **角色卡已更新！主人，準備好開始了嗎？**")
                else:
                    await message.channel.send("❌ 主人，請告訴我具體的設定內容。")
                return

            # 指令：獲取角色卡
            if message.content == "!getchar":
                char = user_characters.get(message.author.id, DEFAULT_CHARACTER)
                await message.channel.send(f"📋 **目前的設定如下：**\n{char}")
                return

            # --- AI 對話邏輯 ---
            async with message.channel.typing():
                try:
                    char_prompt = user_characters.get(message.author.id, DEFAULT_CHARACTER)
                    
                    # 抓取最近 10 條對話紀錄
                    history = []
                    async for msg in message.channel.history(limit=10):
                        role = "assistant" if msg.author == self.user else "user"
                        history.append({"role": role, "content": msg.content})
                    history.reverse()

                    # 調用 OpenRouter API
                    response = requests.post(
                        url="https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {OPENROUTER_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "neversleep/llama-3-lumimaid-70b", # 最強 RP 模型
                            "messages": [{"role": "system", "content": char_prompt}] + history,
                            "temperature": 0.85,
                            "top_p": 0.9,
                            "max_tokens": 1500
                        },
                        timeout=45
                    )

                    if response.status_code == 200:
                        reply = response.json()['choices'][0]['message']['content']
                        await message.channel.send(reply)
                    else:
                        error_msg = response.json().get('error', {}).get('message', '未知錯誤')
                        await message.channel.send(f"⚠️ API 錯誤 ({response.status_code}): {error_msg}")

                except Exception as e:
                    print(f"Error: {e}")
                    await message.channel.send("❌ 哎呀...連線好像斷掉了，主人請再試一次。")

# 啟動機器人
intents = discord.Intents.default()
intents.message_content = True
client = MyBot(intents=intents)
client.run(TOKEN)