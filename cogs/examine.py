import discord
from discord import app_commands
from discord.ext import commands
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
ABUSE_API = os.getenv("ABUSE_API")


# ------------------ NEW LOCAL SECURITY FUNCTIONS ------------------

def calculate_entropy(string):
    prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
    entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
    return entropy

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

def check_suspicious_tld(domain):
    risky = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top"]
    return any(domain.endswith(tld) for tld in risky)

def check_subdomain_abuse(domain):
    return len(domain.split(".")) > 3

def check_suspicious_keywords(url):
    keywords = ["login", "verify", "account", "bank", "secure", "update", "password"]
    return any(word in url.lower() for word in keywords)

def check_url_length(url):
    return len(url) > 120


# ------------------------------------------------------------------

class LinkScan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        # ---------------- HOMOGRAPH ----------------
        try:
            idna.encode(domain).decode("ascii")
        except:
            score -= 25
            findings.append("📁 Unicode domain (Homograph Risk)")

        # ---------------- DNS ANALYSIS (NEW) ----------------
        dns_data = check_dns_records(domain)

        if not dns_data["mx"]:
            score -= 10
            findings.append("📁 ไม่มี MX Record")

        if not dns_data["txt"]:
            score -= 5
            findings.append("📁 ไม่มี SPF/TXT Record")

        # ---------------- TLD CHECK (NEW) ----------------
        if check_suspicious_tld(domain):
            score -= 15
            findings.append("📁 ใช้ TLD เสี่ยง")

        # ---------------- SUBDOMAIN ABUSE (NEW) ----------------
        if check_subdomain_abuse(domain):
            score -= 10
            findings.append("📁 Subdomain ซ้อนหลายชั้น")

        # ---------------- ENTROPY CHECK (NEW) ----------------
        entropy = calculate_entropy(domain.replace(".", ""))
        if entropy > 4:
            score -= 15
            findings.append("📁 Domain entropy สูง (ชื่อมั่ว)")

        # ---------------- KEYWORD CHECK (NEW) ----------------
        if check_suspicious_keywords(url):
            score -= 10
            findings.append("📁 พบคำเสี่ยงใน URL")

        # ---------------- URL LENGTH (NEW) ----------------
        if check_url_length(url):
            score -= 10
            findings.append("📁 URL ยาวผิดปกติ")

        # ---------------- WHOIS AGE ----------------
        try:
            loop = asyncio.get_running_loop()
            w = await loop.run_in_executor(None, whois.whois, domain)
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
                    findings.append("💢 โดเมนอายุน้อยกว่า 30 วัน")
        except:
            pass

        # ---------------- SSL CHECK ----------------
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
                findings.append("🚨 SSL ตรวจสอบไม่ผ่าน")
        else:
            score -= 25
            findings.append("🚨 ไม่มี HTTPS")

        # ---------------- FINAL SCORE ----------------
        if score >= 80:
            level = "🍐 ปลอดภัยสูง"
            color = discord.Color.green()
        elif score >= 50:
            level = "🍋 ปานกลาง"
            color = discord.Color.orange()
        else:
            level = "🌶️ อันตรายสูง"
            color = discord.Color.red()

        embed = discord.Embed(
            title="📁 Advanced AI Threat Intelligence Report",
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