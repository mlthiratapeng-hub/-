import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
import hashlib
import socket
import ssl
import idna
import re
import whois
from urllib.parse import urlparse
from datetime import datetime, timezone

ALLOWED_GUILD_ID = 1476624073990738022
ALLOWED_CHANNEL_ID = 1476914330854490204

VT_API = os.getenv("VT_API")
GSB_API = os.getenv("GSB_API")
ABUSE_API = os.getenv("ABUSE_API")

class LinkScan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="examine", description="Advanced AI Threat Scan")
    async def examine(self, interaction: discord.Interaction, url: str):

        if interaction.guild_id != ALLOWED_GUILD_ID:
            await interaction.response.send_message("🍒 ใช้ได้เฉพาะเซิฟเวอร์ที่กำหนด", ephemeral=True)
            return

        if interaction.channel_id != ALLOWED_CHANNEL_ID:
            await interaction.response.send_message("🥩 ใช้ได้เฉพาะห้องที่กำหนด", ephemeral=True)
            return

        await interaction.response.defer()

        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            await interaction.followup.send("🍎 URL ไม่ถูกต้อง")
            return

        domain = parsed.netloc.lower()
        score = 100
        findings = []

        # ----------------- Homograph -----------------
        try:
            idna.encode(domain).decode("ascii")
        except:
            score -= 25
            findings.append("⚠️ Unicode domain (Homograph Risk)")

        # ----------------- WHOIS Age -----------------
        try:
            w = whois.whois(domain)
            creation = w.creation_date
            if isinstance(creation, list):
                creation = creation[0]

            if creation:
                age_days = (datetime.now(timezone.utc) - creation.replace(tzinfo=timezone.utc)).days
                if age_days < 7:
                    score -= 30
                    findings.append("🚨 โดเมนอายุน้อยกว่า 7 วัน")
                elif age_days < 30:
                    score -= 15
                    findings.append("💾 โดเมนอายุน้อยกว่า 30 วัน")
        except:
            findings.append("ℹ️ ไม่สามารถตรวจอายุโดเมนได้")

        # ----------------- SSL Check -----------------
        if parsed.scheme == "https":
            try:
                ctx = ssl.create_default_context()
                with socket.create_connection((domain, 443), timeout=5) as sock:
                    with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        if not cert:
                            score -= 20
                            findings.append("🚨 SSL ผิดปกติ")
            except:
                score -= 20
                findings.append("🍇 SSL ตรวจสอบไม่ผ่าน")
        else:
            score -= 25
            findings.append("🚨 ไม่มี HTTPS")

        async with aiohttp.ClientSession() as session:

            # ----------------- Redirect Analysis -----------------
            try:
                async with session.get(url, allow_redirects=True, timeout=10) as resp:
                    if len(resp.history) > 2:
                        score -= 15
                        findings.append("🍃 Redirect หลายชั้น")

                    html = await resp.text()

                    # -------- Form Phishing Analysis --------
                    if re.search(r'<input[^>]+type=["\']password["\']', html, re.I):
                        if any(x in domain for x in ["login", "secure", "verify"]):
                            score -= 25
                            findings.append("🚨 มีฟอร์มกรอกรหัสผ่าน (เสี่ยง phishing)")
            except:
                pass

            # ----------------- IP Reputation -----------------
            try:
                ip = socket.gethostbyname(domain)
                headers = {"Key": ABUSE_API, "Accept": "application/json"}
                async with session.get(
                    f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90",
                    headers=headers
                ) as resp:
                    data = await resp.json()
                    abuse_score = data["data"]["abuseConfidenceScore"]
                    if abuse_score > 50:
                        score -= 25
                        findings.append("🚨 IP Reputation เสี่ยงสูง")
                    elif abuse_score > 20:
                        score -= 10
                        findings.append("🍃 IP Reputation น่าสงสัย")
            except:
                pass

            # ----------------- VirusTotal -----------------
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
                            findings.append(f"🚨 VirusTotal พบมัลแวร์ {malicious}")
                        elif suspicious > 0:
                            score -= 30
                            findings.append(f"🍃 VirusTotal น่าสงสัย {suspicious}")
            except:
                findings.append("📁 ไม่สามารถเช็ค VirusTotal ได้")

            # ----------------- Google Safe Browsing -----------------
            try:
                body = {
                    "client": {"clientId": "bot", "clientVersion": "1.0"},
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
                        findings.append("🚨 Google Safe Browsing พบภัย")
            except:
                findings.append("📁 ไม่สามารถเช็ค Google ได้")

        # ----------------- AI Heuristic Final -----------------
        if score >= 80:
            level = "🍇 ปลอดภัยสูง"
            color = discord.Color.green()
        elif score >= 50:
            level = "🌻 ปานกลาง"
            color = discord.Color.orange()
        else:
            level = "💢 อันตรายสูง"
            color = discord.Color.red()

        embed = discord.Embed(
            title="🛡 Advanced AI Threat Intelligence Report",
            color=color,
            timestamp=datetime.now()
        )

        embed.add_field(name="โดเมน", value=domain, inline=False)
        embed.add_field(name="คะแนน AI", value=f"{score}/100\n{level}", inline=False)

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