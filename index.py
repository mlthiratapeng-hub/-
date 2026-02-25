import discord
from discord.ext import commands
import aiohttp
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

COOKIE_STRING = "SESSION=NTk1MzdmOTgtZGFkNC00ZTU0LTk3MGItOWMyMzU2ZDRiM2Jl; cookiesession1=678B7767BF4514B0D6A0C1E208A67557; NSXLB.l6zk3Z3Jsv61nBjP/GOWL8YHRiR7HGJ7uAKHSR59YLp69cmCaSY9bHlIrK1betytd1j050x1F8EgtZ8hNIM7BQ=="

ALLOWED_CHANNELS = [1472418594083307540]
REQUIRED_ROLE_IDS = [1476184537674289235]

async def fetch_id(pid: str):
    url = f"https://authenservice.nhso.go.th/authencode/api/nch-personal-fund/search-by-pid?pid={pid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://authenservice.nhso.go.th/authencode/",
        "Cookie": COOKIE_STRING
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=20) as r:
            if r.status in [401, 403]:
                return {"error": "API fail หรือ Cookie หมดอายุ"}
            if r.status == 404:
                return {"error": "ไม่เจอข้อมูลเลขบัตรนี้"}
            if r.status != 200:
                return {"error": f"Error {r.status}"}
            return await r.json()

def zick_embed(data, pid):
    p = data.get("personData", {})
    main = data.get("mainInscl", {}).get("rightName", "ไม่เจอ")
    sub = data.get("subInscl", {}).get("codeWithName", "ไม่เจอ")
    sex = "ชาย" if p.get("sex") == "1" else "หญิง" if p.get("sex") == "2" else "ไม่เจอ"
    addr = p.get("addressCatm", {})
    home = p.get("homeAddress", {})

    # ดึงเบอร์โทรศัพท์
    phone = (
        p.get("mobileNo") or
        p.get("telephone") or
        p.get("phone") or
        p.get("mobile") or
        "N/A"
    )

    embed = discord.Embed(
        title="ข้อมูลสำคัญจาก NHSO",
        color=#FFFAFA
    )

    # I. ข้อมูลบุคคล
    embed.add_field(
        name="I. ข้อมูลบุคคล (Identity)",
        value=f"```yaml\nชื่อ-นามสกุล: {p.get('fullName', 'ไม่เจอ')}\n"
              f"เลขบัตรประชาชน: {p.get('pid', 'N/A')}\n"
              f"วันเกิด/อายุ: {p.get('displayBirthDate', '-')} ({p.get('age', {}).get('years', '?')} ปี)\n"
              f"เพศ: {sex}\n```",
        inline=False
    )

    # II. ข้อมูลการมีสิทธิ์
    embed.add_field(
        name="II. ข้อมูลการมีสิทธิ์",
        value=f"```yaml\nสิทธิหลัก: {main}\nสิทธิรอง: {sub}\n```",
        inline=False
    )

    # III. ข้อมูลที่อยู่
    embed.add_field(
         name="III. ข้อมูลที่อยู่ (Address Detail)",
        value=f"```yaml\nที่อยู่ CATM: {addr.get('adressFullTh', 'ไม่เจอ')}\n"
              f"บ้านเลขที่: {home.get('adressNo', 'N/A')} หมู่ {addr.get('moo', '-')}\n"
              f"ตำบล: {addr.get('tumbonName', 'ไม่เจอ')}\n"
              f"อำเภอ: {addr.get('amphurName', 'ไม่เจอ')}\n"
              f"จังหวัด: {addr.get('changwatName', 'ไม่เจอ')}\n```",
        inline=False
    )

    # IV. ข้อมูลติดต่อ (ใหม่!)
    embed.add_field(
        name="IV. ข้อมูลติดต่อ",
        value=f"```yaml\nเบอร์โทรศัพท์: {phone}\n```",
        inline=False
    )

    embed.set_footer(text="ดึงข้อมูล สปสช")

    return embed

@bot.command(name="id")
@commands.cooldown(1, 8, commands.BucketType.user)
async def id_lookup(ctx, pid: str):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return await ctx.send("ใช้ได้เเค่ช่องที่กูให้ใช้เท่านั้นไอ้วควาย", delete_after=5)
    if not any(role.id in REQUIRED_ROLE_IDS for role in ctx.author.roles):
        return await ctx.send("ชั้นต่ำอยากใช้คำสั่งชั้นสูง", delete_after=5)
    if not (pid.isdigit() and len(pid) == 13):
        return await ctx.send("ใส่เลขบัตรประชาชน 13 หลัก", delete_after=5)

    msg = await ctx.send("กำลังค้นหาข้อมูล สปสช")
    data = await fetch_id(pid)

    if "error" in data:
        await msg.edit(content=f"```{data['error']}```")
    else:
        await msg.edit(content=None, embed=zick_embed(data, pid))

  import os
bot.run(os.getenv("BOTTOKEN"))