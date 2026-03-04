import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import os
import socket
import ssl
import math
import dns.resolver
import asyncio

from urllib.parse import urlparse
from datetime import datetime

VT_API = os.getenv("VT_API")
GSB_API = os.getenv("GSB_API")

# ================= BLACKLIST CACHE =================

blacklist_cache = set()

async def update_blacklist():
    global blacklist_cache
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("https://urlhaus.abuse.ch/downloads/text/") as resp:
                text = await resp.text()
                blacklist_cache = set(
                    line.strip()
                    for line in text.splitlines()
                    if line and not line.startswith("#")
                )
    except Exception as e:
        print(f"[BLACKLIST ERROR] {e}")

# ================= REDIRECT + SHORTENER =================

SHORTENERS = [
    "bit.ly", "tinyurl.com", "t.co",
    "rebrand.ly", "cutt.ly", "goo.gl",
    "is.gd", "buff.ly"
]

async def expand_and_trace(url):
    redirect_chain = []
    final_url = url

    timeout = aiohttp.ClientTimeout(total=15)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, allow_redirects=True) as resp:
                for r in resp.history:
                    redirect_chain.append(str(r.url))
                final_url = str(resp.url)
    except Exception as e:
        print(f"[REDIRECT ERROR] {e}")

    return final_url, redirect_chain

# ================= SSL CHECK =================

def check_ssl(domain):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                expire_date = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                if expire_date < datetime.utcnow():
                    return False, "ใบรับรอง SSL หมดอายุ"
        return True, None
    except Exception:
        return False, "SSL ผิดปกติหรือไม่มี"

# ================= DNS CHECK =================

def dns_scan(domain):
    issues = []
    try:
        dns.resolver.resolve(domain, 'A')
    except:
        issues.append("ไม่มี A record")

    try:
        dns.resolver.resolve(domain, 'MX')
    except:
        issues.append("ไม่มี MX record")

    return issues

# ================= DOMAIN ENTROPY =================

def calculate_entropy(domain):
    prob = [float(domain.count(c)) / len(domain) for c in dict.fromkeys(list(domain))]
    entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
    return entropy

# ================= VIRUSTOTAL =================

async def check_virustotal(url):
    if not VT_API:
        return 0, 0

    headers = {"x-apikey": VT_API}
    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
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

    except Exception as e:
        print(f"[VT ERROR] {e}")
        return 0, 0

# ================= GOOGLE SAFE =================

async def check_google_safe(url):
    if not GSB_API:
        return False

    payload = {
        "client": {"clientId": "discord-bot", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }

    timeout = aiohttp.ClientTimeout(total=15)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GSB_API}",
                json=payload
            ) as resp:
                result = await resp.json()

        return "matches" in result

    except Exception as e:
        print(f"[GSB ERROR] {e}")
        return False

# ================= BOT CLASS =================

class LinkScan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_update.start()

    @tasks.loop(hours=1)
    async def auto_update(self):
        await update_blacklist()

    @app_commands.command(name="examine", description="เช็คลิ้งความปลอดภัยมาตรฐานgoogle")
    async def examine(self, interaction: discord.Interaction, url: str):

        await interaction.response.defer()

        parsed = urlparse(url)

        if parsed.scheme not in ["http", "https"]:
            await interaction.followup.send("URL ต้องขึ้นต้นด้วย http หรือ https")
            return

        domain = parsed.netloc.lower()
        score = 100
        findings = []

        if any(short in domain for short in SHORTENERS):
            score -= 10
            findings.append("🔗 ใช้ URL Shortener")

        final_url, chain = await expand_and_trace(url)

        if len(chain) > 0:
            findings.append(f"↪ มี redirect {len(chain)} ชั้น")
            if len(chain) >= 3:
                score -= 15

        if url in blacklist_cache:
            score -= 50
            findings.append("🌶️ พบใน URLHaus Blacklist")

        ssl_ok, ssl_issue = check_ssl(domain)
        if not ssl_ok:
            score -= 10
            findings.append(f"📁 {ssl_issue}")

        dns_issues = dns_scan(domain)
        if dns_issues:
            score -= 10
            findings.extend([f"🌐 {i}" for i in dns_issues])

        entropy = calculate_entropy(domain.replace(".", ""))
        if entropy > 4.0:
            score -= 10
            findings.append("🍲 โดเมนสุ่มสูงผิดปกติ")

        mal, sus = await check_virustotal(url)
        if mal > 0:
            score -= mal * 15
            findings.append(f"🚨 VirusTotal malicious {mal}")
        elif sus > 0:
            score -= sus * 8
            findings.append(f"⚠️ VirusTotal suspicious {sus}")

        if await check_google_safe(url):
            score -= 40
            findings.append("🚨 Google Safe Browsing ระบุว่าอันตราย")

        score = max(score, 0)

        if score >= 80:
            level = "🍇 ปลอดภัยสูง"
            color = discord.Color.green()
        elif score >= 50:
            level = "🍋 ปานกลาง"
            color = discord.Color.orange()
        else:
            level = "🌶 อันตรายสูง"
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

# โหลด Cog แบบ Global (ทุกเซิร์ฟ)

async def setup(bot):
    await bot.add_cog(LinkScan(bot))