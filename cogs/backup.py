import discord
from discord.ext import commands
from discord import app_commands
import json
import os


class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # เช็คว่าเป็นเจ้าของเซิร์ฟไหม
    # =========================
    def is_owner(self, interaction: discord.Interaction):
        return interaction.user.id == interaction.guild.owner_id

    # =========================
    # /safe (Owner only)
    # =========================
    @app_commands.command(name="setbackup", description="สำรองโครงสร้างห้องทั้งหมด (เฉพาะหัวดิส)")
    async def safe(self, interaction: discord.Interaction):

        if not self.is_owner(interaction):
            return await interaction.response.send_message(
                "🌶️ คำสั่งนี้ใช้ได้เฉพาะเจ้าของเซิร์ฟเวอร์เท่านั้น",
                ephemeral=True
            )

        guild = interaction.guild
        data = {
            "categories": [],
            "channels": []
        }

        # เก็บหมวดหมู่
        for category in guild.categories:
            data["categories"].append({
                "name": category.name,
                "position": category.position
            })

        # เก็บห้อง
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                data["channels"].append({
                    "name": channel.name,
                    "type": "text",
                    "category": channel.category.name if channel.category else None
                })

            elif isinstance(channel, discord.VoiceChannel):
                data["channels"].append({
                    "name": channel.name,
                    "type": "voice",
                    "category": channel.category.name if channel.category else None
                })

        with open(f"backup_{guild.id}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        await interaction.response.send_message(
            "🍃 สำรองโครงสร้างเซิร์ฟเวอร์เรียบร้อยแล้ว",
            ephemeral=True
        )

    # =========================
    # /restore (Owner only)
    # =========================
    @app_commands.command(name="restore", description="กู้คืนโครงสร้างจาก backup (เฉพาะหัวดิส)")
    async def restore(self, interaction: discord.Interaction):

        if not self.is_owner(interaction):
            return await interaction.response.send_message(
                "🌶️ คำสั่งนี้ใช้ได้เฉพาะเจ้าของเซิร์ฟเวอร์เท่านั้น",
                ephemeral=True
            )

        guild = interaction.guild
        file_name = f"backup_{guild.id}.json"

        if not os.path.exists(file_name):
            return await interaction.response.send_message(
                "🍅 ไม่พบไฟล์ backup",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)

        # ลบทุกห้อง
        for channel in guild.channels:
            try:
                await channel.delete()
            except:
                pass

        # สร้างหมวดหมู่ใหม่
        category_map = {}
        for cat in data["categories"]:
            new_cat = await guild.create_category(cat["name"])
            category_map[cat["name"]] = new_cat

        # สร้างห้องใหม่
        for ch in data["channels"]:
            category = category_map.get(ch["category"])

            if ch["type"] == "text":
                await guild.create_text_channel(ch["name"], category=category)

            elif ch["type"] == "voice":
                await guild.create_voice_channel(ch["name"], category=category)

        await interaction.followup.send(
            "♻️ กู้คืนโครงสร้างสำเร็จ",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Backup(bot))