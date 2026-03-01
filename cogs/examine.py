import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import os
import socket
import ssl
import idna
import re
import whois
import asyncio
import base64
import math
import dns.resolver

from collections import Counter
from urllib.parse import urlparse
from datetime import datetime, timezone

ALLOWED_GUILD_ID = 1476624073990738022
ALLOWED_CHANNEL_ID = 1476914330854490204

VT_API = os.getenv("VT_API")
GSB_API = os.getenv("GSB_API")

# ================= BLACKLIST CACHE =================

blacklist_cache = set()

async def update_blacklist():
    global blacklist_cache
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://urlhaus.abuse.ch/downloads/text/") as resp:
                text = await resp.text()
                blacklist_cache = set(
                    line.strip()
                    for line in text.splitlines()
                    if line and not line.startswith("#")
                )
    except:
        pass

# ================= VIRUSTOTAL =================

async def check_virustotal(url):
    if not VT_API:
        return 0, 0

    headers = {"x-apikey": VT_API}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data={"url": url}
        ) as resp:
            data = await resp.json()

        url_id = data["data"]["id"]

        async with session.get(
            f"https://www.virustotal.com/api/v3/analyses/{url_id}",
            headers=headers
        ) as resp:
            result = await resp.json()

    stats = result["data"]["attributes"]["stats"]
    return stats.get("malicious", 0), stats.get("suspicious", 0)

# ================= GOOGLE SAFE BROWSING =================

async def check_google_safe(url):
    if not GSB_API:
        return False

    payload = {
        "client": {
            "clientId": "discord-bot",
            "clientVersion": "1.0"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GSB_API}",
            json=payload
        ) as resp:
            result = await resp.json()

    return "matches" in result

# ================= ENTROPY =================

def calculate_entropy(string):
    prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
    entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
    return entropy

# ================= DNS =================

def check_dns_records(domain):
    results = {"mx": [], "ns": [], "txt": []}
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        results["mx"] = [r.exchange.to_text() for r in answers]
    except:
        pass
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        results["ns"] = [r.to_text() for r in answers]
    except:
        pass
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        results["txt"] = [r.to_text() for r in answers]
    except:
        pass
    return results

# ================= BOT CLASS =================

class LinkScan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_update.start()

    @tasks.loop(hours=1)
    async def auto_update(self):
        await update_blacklist()

    @app_commands.command(name="examine", description="Advanced AI Threat Scan")
    async def examine(self, interaction: discord.Interaction, url: str):

        if interaction.guild_id != ALLOWED_GUILD_ID:
            await interaction.response.send_message("ใช้ได้เฉพาะเซิร์ฟเวอร์ที่กำหนด", ephemeral=True)
            return

        if interaction.channel_id != ALLOWED_CHANNEL_ID:
            await interaction.response.send_message("ใช้ได้เฉพาะห้องที่กำหนด", ephemeral=True)
            return

        await interaction.response.defer()

        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            await interaction.followup.send("URL ต้องขึ้นต้นด้วย http หรือ https")
            return

        domain = parsed.netloc.lower()
        score = 100
        findings = []

        # ============ BLACKLIST ============
        if url in blacklist_cache:
            score -= 50
            findings.append("🚨 พบใน URLHaus Blacklist")

        # ============ VIRUSTOTAL ============
        try:
            mal, sus = await check_virustotal(url)
            if mal > 0:
                score -= mal * 15
                findings.append(f"🚨 VirusTotal malicious {mal}")
            elif sus > 0:
                score -= sus * 8
                findings.append(f"⚠ VirusTotal suspicious {sus}")
        except:
            pass

        # ============ GOOGLE SAFE ============
        try:
            if await check_google_safe(url):
                score -= 40
                findings.append("🚨 Google Safe Browsing ระบุว่าอันตราย")
        except:
            pass

        # ============ FINAL LEVEL ============
        if score >= 80:
            level = "🍇 ปลอดภัยสูง"
            color = discord.Color.green()
        elif score >= 50:
            level = "🍋 ปานกลาง"
            color = discord.Color.orange()
        else:
            level = "🌶️ อันตรายสูง"
            color = discord.Color.red()

        embed = discord.Embed(
            title="Advanced AI Threat Intelligence Report",
            color=color,
            timestamp=datetime.now()
        )

        embed.add_field(name="โดเมน", value=domain, inline=False)
        embed.add_field(name="คะแนน", value=f"{score}/100\n{level}", inline=False)

        if findings:
            embed.add_field(name="ผลการวิเคราะห์", value="\n".join(findings), inline=False)
        else:
            embed.add_field(name="ผลการวิเคราะห์", value="ไม่พบพฤติกรรมเสี่ยง", inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(
        LinkScan(bot),
        guild=discord.Object(id=ALLOWED_GUILD_ID)
    )