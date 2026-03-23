import discord
from discord.ext import commands
from discord import app_commands

# ====== VIEW ปุ่ม ======
class RoleView(discord.ui.View):
    def __init__(self, roles_data):
        super().__init__(timeout=None)

        for data in roles_data:
            role_id = data["role_id"]
            label = data["label"]
            emoji = data["emoji"]

            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=discord.ButtonStyle.success,
                custom_id=f"role_{role_id}"
            )

            async def callback(interaction: discord.Interaction, role_id=role_id):
                role = interaction.guild.get_role(role_id)

                if not role:
                    return await interaction.response.send_message("🌪️ ไม่เจอยศ", ephemeral=True)

                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(
                        f"🧨 เอายศ {role.name} ออกแล้ว", ephemeral=True
                    )
                else:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(
                        f"🌎 ได้รับยศ {role.name} แล้ว", ephemeral=True
                    )

            button.callback = callback
            self.add_item(button)

# ====== COG ======
class ReceiveRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="vdena_rank", description="สร้างปุ่มรับยศ")
    async def receiverole(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        image_url: str = None,  # 🔥 ใส่ GIF/รูปได้ (หรือไม่ใส่ก็ได้)

        role1: discord.Role = None, label1: str = None, emoji1: str = None,
        role2: discord.Role = None, label2: str = None, emoji2: str = None,
        role3: discord.Role = None, label3: str = None, emoji3: str = None,
        role4: discord.Role = None, label4: str = None, emoji4: str = None,
        role5: discord.Role = None, label5: str = None, emoji5: str = None,
        role6: discord.Role = None, label6: str = None, emoji6: str = None,
        role7: discord.Role = None, label7: str = None, emoji7: str = None,
        role8: discord.Role = None, label8: str = None, emoji8: str = None,
        role9: discord.Role = None, label9: str = None, emoji9: str = None,
        role10: discord.Role = None, label10: str = None, emoji10: str = None,
    ):
        roles_data = []

        def add_role(role, label, emoji):
            if role and label and emoji:
                roles_data.append({
                    "role_id": role.id,
                    "label": label,
                    "emoji": emoji
                })

        add_role(role1, label1, emoji1)
        add_role(role2, label2, emoji2)
        add_role(role3, label3, emoji3)
        add_role(role4, label4, emoji4)
        add_role(role5, label5, emoji5)
        add_role(role6, label6, emoji6)
        add_role(role7, label7, emoji7)
        add_role(role8, label8, emoji8)
        add_role(role9, label9, emoji9)
        add_role(role10, label10, emoji10)

        if len(roles_data) == 0:
            return await interaction.response.send_message("🍅 ต้องมีอย่างน้อย 1 ยศ", ephemeral=True)

        # ====== EMBED ======
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.random()
        )

        text = ""
        for r in roles_data:
            role = interaction.guild.get_role(r["role_id"])
            text += f"{r['emoji']} | {role.mention}\n"

        embed.add_field(name="📌 เลือกยศ", value=text, inline=False)

        # 🔥 ใส่ GIF / รูป (ถ้ามี)
        if image_url:
            embed.set_image(url=image_url)

        view = RoleView(roles_data)

        await interaction.response.send_message(embed=embed, view=view)

# ====== SETUP ======
async def setup(bot):
    await bot.add_cog(ReceiveRole(bot))