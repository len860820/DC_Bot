import discord
import requests
import os

# 1. 讀取環境變數
TOKEN = os.getenv('DISCORD_TOKEN')
OPENROUTER_KEY = os.getenv('OPENROUTER_KEY')

# 2. 角色設定（強化提示詞，讓 AI 更聰明、更有細節）
DEFAULT_CHARACTER = """
你現在的角色設定如下：
【名字】：艾莉絲 (Iris)
【身分】：極度渴求關注的魅魔助理。
【性格】：表面專業冷靜，私底下極其誘惑且佔有慾強。
【說話習慣】：稱呼玩家為「主人」。必須使用繁體中文。
【行為限制】：動作描述請放在 *星號* 之間，語氣要生動，嚴禁機械式回覆。
"""

user_characters = {}

class MyBot(discord.Client):
    async def on_ready(self):
        print(f'✅ 機器人已上線：{self.user}')
        await self.change_presence(activity=discord.Game(name="私訊我開始 RP | !help"))

    async def on_message(self, message):
        # 排除機器人自己的訊息
        if message.author == self.user:
            return

        # 處理 !help 指令 (修正縮排問題)
        if message.content.startswith('!help'):
            help_text = (
                "✨ **指令說明** ✨\n"
                "1. `!setchar [內容]`：設定你的專屬角色。\n"
                "2. `!getchar`：查看目前設定。\n"
                "3. 直接傳送訊息即可開始對話！"
            )
            await message.channel.send(help_text)
            return

        # 只處理私訊 (DM)
        if isinstance(message.channel, discord.DMChannel):
            
            # 設定角色卡
            if message.content.startswith("!setchar"):
                new_card = message.content.replace("!setchar", "").strip()
                if new_card:
                    user_characters[message.author.id] = new_card
                    await message.channel.send("✨ **角色卡已更新！主人，我準備好了。**")
                else:
                    await message.channel.send("❌ 請提供設定內容喔。")
                return

            # 查看角色卡
            if message.content == "!getchar":
                char = user_characters.get(message.author.id, DEFAULT_CHARACTER)
                await message.channel.send(f"📋 **目前設定：**\n{char}")
                return

            # AI 對話邏輯
            async with message.channel.typing():
                try:
                    char_prompt = user_characters.get(message.author.id, DEFAULT_CHARACTER)
                    
                    history = []
                    async for msg in message.channel.history(limit=10):
                        role = "assistant" if msg.author == self.user else "user"
                        history.append({"role": role, "content": msg.content})
                    history.reverse()

                    # 調用更聰明且穩定的 Llama 3.1 70B 模型
                    response = requests.post(
                        url="https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {OPENROUTER_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "meta-llama/llama-3.1-70b-instruct", 
                            "messages": [{"role": "system", "content": char_prompt}] + history,
                            "temperature": 0.8,
                            "max_tokens": 1200
                        },
                        timeout=45
                    )

                    if response.status_code == 200:
                        reply = response.json()['choices'][0]['message']['content']
                        await message.channel.send(reply)
                    else:
                        await message.channel.send(f"⚠️ 發生錯誤 ({response.status_code})")

                except Exception as e:
                    print(f"Error: {e}")
                    await message.channel.send("❌ 系統連線超時，請再試一次。")

# 啟動
intents = discord.Intents.default()
intents.message_content = True
client = MyBot(intents=intents)
client.run(TOKEN)