import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from flask import Flask # ต้องใช้สำหรับ 24/7
from threading import Thread # ต้องใช้สำหรับ 24/7

# --- ส่วนของระบบ Keep Alive (ห้ามลบ) ---
app = Flask('')

@app.route('/')
def home():
    return "บอทออนไลน์แล้ว!"

def run_http():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()
# ---------------------------------------

# --- ตั้งค่า TOKEN และ ID ห้อง Log ---
TOKEN = 'MTQ3NTAyOTA4MDQ2NTQ3MzY1OQ.GX2Kwv.F89jXSasAh969hzyIxKM5CqKc0ur8rZKiZqu1k'
LOG_CHANNEL_ID = 123456789012345678 

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("⏳ กำลังเชื่อมต่อคำสั่ง Slash Command...")
        try:
            synced = await self.tree.sync()
            print(f"✅ Sync สำเร็จ! ทั้งหมด {len(synced)} คำสั่ง")
        except Exception as e:
            print(f"❌ Sync ล้มเหลว: {e}")

bot = MyBot()
sticky_data = {}

@bot.event
async def on_ready():
    print(f'🤖 บอท {bot.user} ออนไลน์แล้ว!')
    print(f'⚙️ สถานะ Message Content Intent: {bot.intents.message_content}')

# --- 1. คำสั่ง /help ---
@bot.tree.command(name="help", description="ดูวิธีใช้งานบอททั้งหมด")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="📚 คู่มือ Seasun Sticky", color=0xf1c40f)
    embed.add_field(name="`/message`", value="ตั้งค่าปักหมุด (เลือกห้องได้)", inline=False)
    embed.add_field(name="`/delete`", value="ยกเลิกปักหมุดในห้องนี้", inline=False)
    embed.set_footer(text="หากไม่เห็นคำสั่ง ให้ลองปิด-เปิด Discord ใหม่")
    await interaction.response.send_message(embed=embed)

# --- 2. คำสั่ง /message ---
@bot.tree.command(name="message", description="ตั้งค่าข้อความปักหมุด")
@app_commands.describe(text="ข้อความที่ต้องการ", channel="ห้องที่ต้องการ (ถ้าไม่เลือกจะใช้ห้องปัจจุบัน)")
async def message(interaction: discord.Interaction, text: str, channel: discord.TextChannel = None):
    target_channel = channel if channel else interaction.channel
    sticky_data[target_channel.id] = {"content": text, "last_id": None}
    await interaction.response.send_message(f"✅ เริ่มปักหมุดที่ {target_channel.mention}", ephemeral=True)
    msg = await target_channel.send(text)
    sticky_data[target_channel.id]["last_id"] = msg.id

# --- 3. คำสั่ง /delete ---
@bot.tree.command(name="delete", description="ยกเลิกปักหมุด")
async def delete(interaction: discord.Interaction):
    if interaction.channel_id in sticky_data:
        del sticky_data[interaction.channel_id]
        await interaction.response.send_message("🗑️ ยกเลิกปักหมุดเรียบร้อย!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ ห้องนี้ไม่มีการปักหมุดอยู่", ephemeral=True)

# --- 4. ระบบตรวจจับข้อความซ้ำ + ไหล Sticky ---
@bot.event
async def on_message(message):
    if message.author.bot: return

    # ส่วนที่ 1: ตรวจจับข้อความซ้ำ (Anti-Duplicate)
    async for history in message.channel.history(limit=5):
        if history.id != message.id and \
           history.author == message.author and \
           history.content.strip() == message.content.strip() and \
           message.content.strip() != "":
            try:
                await message.delete()
                print(f"🗑️ ลบข้อความซ้ำของ {message.author}")
                return 
            except: pass

    # ส่วนที่ 2: ระบบไหล Sticky
    if message.channel.id in sticky_data:
        data = sticky_data[message.channel.id]
        if data["last_id"]:
            try:
                old_msg = await message.channel.fetch_message(data["last_id"])
                await old_msg.delete()
            except: pass
        
        try:
            new_msg = await message.channel.send(data["content"])
            sticky_data[message.channel.id]["last_id"] = new_msg.id
        except: pass

    await bot.process_commands(message)

# --- ส่วนเริ่มต้นการทำงาน (สำคัญสำหรับ 24/7) ---
if __name__ == "__main__":
    keep_alive() # เริ่มต้น Web Server ปลอม
    bot.run(TOKEN) # รันบอท
