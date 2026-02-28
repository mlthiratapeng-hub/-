import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
import hashlib
from urllib.parse import urlparse

ALLOWED_GUILD_ID = 1476624073990738022
ALLOWED_CHANNEL_ID = 1476914330854490204

VT_API = os.getenv("VT_API")
GSB_API = os.getenv("GSB_API")

class LinkScan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="examine", description="สแกนลิงก์แบบจากGoogle Safe BrowsingเเละVirusTotal")
    @app_commands.describe(url="ลิงก์ที่ต้องการตรวจสอบ")
    async def link(self, interaction: discord.Interaction, url: str):

        if interaction.guild_id != ALLOWED_GUILD_ID:
            await interaction.response.send_message("💢 ใช้ได้เฉพาะเซิฟหน้าโปรบอทค่ะ", ephemeral=True)
            return

        if interaction.channel_id != ALLOWED_CHANNEL_ID:
            await interaction.response.send_message("💢 ใช้ได้เฉพาะห้องที่กำหนดค่ะ", ephemeral=True)
            return

        await interaction.response.defer()

        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            await interaction.followup.send("💢 URL ไม่ถูกต้อง")
            return

        vt_result = "ไม่พบข้อมูล"
        gsb_result = "ไม่พบอันตราย"
        score = 100

        async with aiohttp.ClientSession() as session:

            # -------- VirusTotal --------
            try:
                url_id = hashlib.sha256(url.encode()).hexdigest()
                headers = {"x-apikey": VT_API}

                async with session.get(
                    f"https://www.virustotal.com/api/v3/urls/{url_id}",
                    headers=headers
                ) as resp:

                    if resp.status == 200:
                        data = await resp.json()
                        stats = data["data"]["attributes"]["last_analysis_stats"]

                        malicious = stats.get("malicious", 0)
                        suspicious = stats.get("suspicious", 0)

                        if malicious > 0:
                            score -= 60
                            vt_result = f"💢 ตรวจพบมัลแวร์ {malicious} รายการ"
                        elif suspicious > 0:
                            score -= 30
                            vt_result = f"📁 มีความน่าสงสัย {suspicious} รายการ"
                        else:
                            vt_result = "🍇 ไม่พบมัลแวร์"
            except:
                vt_result = "ไม่สามารถเช็ค VirusTotal ได้"

            # -------- Google Safe Browsing --------
            try:
                body = {
                    "client": {
                        "clientId": "yourbot",
                        "clientVersion": "1.0"
                    },
                    "threatInfo": {
                        "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
                        "platformTypes": ["ANY_PLATFORM"],
                        "threatEntryTypes": ["URL"],
                        "threatEntries": [{"url": url}]
                    }
                }

                async with session.post(
                    f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GSB_API}",
                    json=body
                ) as resp:

                    data = await resp.json()
                    if "matches" in data:
                        score -= 50
                        gsb_result = "💢 Google ตรวจพบภัยคุกคาม"
                    else:
                        gsb_result = "🍇 Google ไม่พบภัยคุกคาม"
            except:
                gsb_result = "ไม่สามารถเช็ค Google ได้"

        if score >= 80:
            level = "🍇 ปลอดภัยสูง"
        elif score >= 50:
            level = "📁 เสี่ยงปานกลาง"
        else:
            level = "💢 อันตรายสูง"

        embed = discord.Embed(
            title="🛡 ผลการสแกนลิงก์ขั้นสูง",
            color=discord.Color.red()
        )

        embed.add_field(name="โดเมน", value=parsed.netloc, inline=False)
        embed.add_field(name="VirusTotal", value=vt_result, inline=False)
        embed.add_field(name="Google Safe Browsing", value=gsb_result, inline=False)
        embed.add_field(name="คะแนนความปลอดภัย", value=f"{score}/100\n{level}", inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(LinkScan(bot), guild=discord.Object(id=ALLOWED_GUILD_ID))