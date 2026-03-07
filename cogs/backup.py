import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import base64


class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_owner(self, interaction: discord.Interaction):
        return interaction.user.id == interaction.guild.owner_id

    # =====================
    # BACKUP
    # =====================
    @app_commands.command(name="setbackup", description="สำรองเซิร์ฟทั้งหมด")
    async def setbackup(self, interaction: discord.Interaction):

        if not self.is_owner(interaction):
            return await interaction.response.send_message(
                "🍅 Owner เท่านั้น",
                ephemeral=True
            )

        guild = interaction.guild

        data = {
            "guild": {},
            "roles": [],
            "categories": [],
            "channels": [],
            "emojis": []
        }

        # ===== SERVER INFO =====
        icon_data = None
        if guild.icon:
            icon_bytes = await guild.icon.read()
            icon_data = base64.b64encode(icon_bytes).decode("utf-8")

        data["guild"] = {
            "name": guild.name,
            "icon": icon_data
        }

        # ===== ROLES =====
        for role in guild.roles:
            if role.is_default():
                continue

            data["roles"].append({
                "name": role.name,
                "color": role.color.value,
                "permissions": role.permissions.value,
                "hoist": role.hoist,
                "mentionable": role.mentionable,
                "position": role.position
            })

        # ===== CATEGORIES =====
        for cat in guild.categories:
            data["categories"].append({
                "name": cat.name,
                "position": cat.position
            })

        # ===== CHANNELS =====
        for channel in guild.channels:

            if isinstance(channel, discord.TextChannel):
                data["channels"].append({
                    "name": channel.name,
                    "type": "text",
                    "category": channel.category.name if channel.category else None,
                    "position": channel.position,
                    "topic": channel.topic
                })

            elif isinstance(channel, discord.VoiceChannel):
                data["channels"].append({
                    "name": channel.name,
                    "type": "voice",
                    "category": channel.category.name if channel.category else None,
                    "position": channel.position
                })

        # ===== EMOJIS =====
        for emoji in guild.emojis:

            emoji_bytes = await emoji.read()

            data["emojis"].append({
                "name": emoji.name,
                "image": base64.b64encode(emoji_bytes).decode("utf-8")
            })

        file = f"backup_{guild.id}.json"

        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        await interaction.response.send_message(
            "🍇 สำรองเซิร์ฟเวอร์เรียบร้อย",
            ephemeral=True
        )

    # =====================
    # RESTORE
    # =====================
    @app_commands.command(name="restore", description="กู้คืนเซิร์ฟเวอร์")
    async def restore(self, interaction: discord.Interaction):

        if not self.is_owner(interaction):
            return await interaction.response.send_message(
                "🍅 Owner เท่านั้น",
                ephemeral=True
            )

        guild = interaction.guild
        file = f"backup_{guild.id}.json"

        if not os.path.exists(file):
            return await interaction.response.send_message(
                "🌶️ ไม่พบ backup",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # ===== SERVER NAME =====
        icon_bytes = None
        if data["guild"]["icon"]:
            icon_bytes = base64.b64decode(data["guild"]["icon"])

        await guild.edit(
            name=data["guild"]["name"],
            icon=icon_bytes
        )

        # ===== DELETE CHANNELS =====
        for ch in guild.channels:
            try:
                await ch.delete()
            except:
                pass

        # ===== DELETE ROLES =====
        for role in guild.roles:
            if role.is_default():
                continue
            try:
                await role.delete()
            except:
                pass

        # ===== CREATE ROLES =====
        for role in data["roles"]:
            await guild.create_role(
                name=role["name"],
                color=discord.Color(role["color"]),
                permissions=discord.Permissions(role["permissions"]),
                hoist=role["hoist"],
                mentionable=role["mentionable"]
            )

        # ===== CREATE CATEGORIES =====
        category_map = {}

        for cat in data["categories"]:
            new_cat = await guild.create_category(cat["name"])
            category_map[cat["name"]] = new_cat

        # ===== CREATE CHANNELS =====
        for ch in data["channels"]:

            category = category_map.get(ch["category"])

            if ch["type"] == "text":
                await guild.create_text_channel(
                    ch["name"],
                    category=category,
                    topic=ch["topic"]
                )

            elif ch["type"] == "voice":
                await guild.create_voice_channel(
                    ch["name"],
                    category=category
                )

        # ===== EMOJIS =====
        for emoji in data["emojis"]:

            try:
                image = base64.b64decode(emoji["image"])

                await guild.create_custom_emoji(
                    name=emoji["name"],
                    image=image
                )
            except:
                pass

        await interaction.followup.send(
            "♻️ กู้คืนเซิร์ฟเวอร์สำเร็จ",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Backup(bot))