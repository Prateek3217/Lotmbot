import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import asyncio
import random
import os
from datetime import datetime, timedelta
from aiohttp import web

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ====================== LOTM PATHWAYS DATA ======================
PATHWAYS = {
    "Fool": ["Seer", "Clown", "Magician", "Faceless", "Marionettist", "Bizarro Sorcerer", "Scholar of Yore", "Miracle Invoker", "Attendant of Mysteries", "Fool"],
    "Error": ["Marauder", "Swindler", "Cryptologist", "Prometheus", "Dream Stealer", "Parasite", "Mentor of Deceit", "Trojan Horse of Destiny", "Worm of Time", "Error"],
    "Door": ["Apprentice", "Trickmaster", "Astrologer", "Scribe", "Traveler", "Secrets Sorcerer", "Wanderer", "Planeswalker", "Key of Stars", "Door"],
    "Visionary": ["Spectator", "Telepathist", "Psychiatrist", "Hypnotist", "Dreamwalker", "Manipulator", "Dream Weaver", "Discerner", "Author", "Visionary"],
    "Sun": ["Bard", "Light Suppliant", "Solar High Priest", "Notary", "Priest of Light", "Unshadowed", "Justice Mentor", "Lightseeker", "White Angel", "Sun"],
    "Tyrant": ["Sailor", "Folk of Rage", "Seafarer", "Wind-blessed", "Ocean Songster", "Cataclysmic Interrer", "Sea King", "Calamity", "Thunder God", "Tyrant"],
    "Hanged Man": ["Secrets Suppliant", "Listener", "Shadow Ascetic", "Rose Bishop", "Shepherd", "Black Knight", "Trinity Templar", "Profane Presbyter", "Dark Angel", "Hanged Man"],
    "White Tower": ["Reader", "Student of Ratiocination", "Detective", "Polymath", "Mysticism Magister", "Prophet", "Cognizer", "Wisdom Angel", "Omniscient Eye", "White Tower"],
    "Darkness": ["Sleepless", "Midnight Poet", "Nightmare", "Soul Assurer", "Spirit Warlock", "Nightwatcher", "Horror Bishop", "Servant of Concealment", "Knight of Misfortune", "Darkness"],
    "Death": ["Corpse Collector", "Gravedigger", "Spirit Medium", "Spirit Guide", "Gatekeeper", "Undying", "Ferryman", "Death Consul", "Pale Emperor", "Death"],
    "Twilight Giant": ["Warrior", "Pugilist", "Weapon Master", "Dawn Paladin", "Guardian", "Demon Hunter", "Silver Knight", "Glory", "Hand of God", "Twilight Giant"],
    "Demoness": ["Assassin", "Instigator", "Witch", "Pleasure", "Affliction", "Despair", "Unaging", "Catastrophe", "Apocalypse", "Demoness"],
    "Red Priest": ["Hunter", "Provoker", "Pyromaniac", "Conspirer", "Reaper", "Iron-blooded Knight", "War Bishop", "Weather Warlock", "Conqueror", "Red Priest"],
    "Hermit": ["Mystery Pryer", "Melee Scholar", "Warlock", "Scrolls Professor", "Constellations Master", "Mysticologist", "Clairvoyant", "Sage", "Knowledge Emperor", "Hermit"],
    "Paragon": ["Savant", "Archaeologist", "Appraiser", "Artisan", "Astronomer", "Alchemist", "Arcane Scholar", "Knowledge Magister", "Illuminator", "Paragon"],
    "Wheel of Fortune": ["Monster", "Robot", "Lucky One", "Calamity Priest", "Winner", "Misfortune Mage", "Chaoswalker", "Soothsayer", "Snake of Mercury", "Wheel of Fortune"],
    "Moon": ["Apothecary", "Beast Tamer", "Vampire", "Potions Professor", "Scarlet Scholar", "Shaman King", "High Summoner", "Life-Giver", "Beauty Goddess", "Moon"],
    "Mother": ["Planter", "Doctor", "Harvest Priest", "Biologist", "Druid", "Classical Alchemist", "Pallbearer", "Desolate Matriarch", "Naturewalker", "Mother"],
    "Chained": ["Prisoner", "Lunatic", "Werewolf", "Zombie", "Wraith", "Puppet", "Disciple of Silence", "Ancient Bane", "Abomination", "Chained"],
    "Abyss": ["Criminal", "Unwinged Angel", "Serial Killer", "Devil", "Desire Apostle", "Demon", "Blatherer", "Bloody Archduke", "Filthy Monarch", "Abyss"],
    "Black Emperor": ["Lawyer", "Barbarian", "Briber", "Baron of Corruption", "Mentor of Disorder", "Earl of the Fallen", "Frenzied Mage", "Duke of Entropy", "Prince of Abolition", "Black Emperor"],
    "Justiciar": ["Arbiter", "Sheriff", "Interrogator", "Judge", "Disciplinary Paladin", "Imperative Mage", "Chaos Hunter", "Balancer", "Hand of Order", "Justiciar"]
}

# ====================== PATHWAY SYMBOL COLORS ======================
PATHWAY_COLORS = {
    "Fool": 0xA9A9A9, "Error": 0xC0C0C0, "Door": 0x40E0D0, "Visionary": 0xE6E6FA,
    "Sun": 0xFFD700, "Tyrant": 0x00BFFF, "Hanged Man": 0x8B0000, "White Tower": 0xE6E6FA,
    "Darkness": 0x4B0082, "Death": 0x2F4F4F, "Twilight Giant": 0xFF4500,
    "Demoness": 0xC71585, "Red Priest": 0xB22222, "Hermit": 0x483D8B,
    "Paragon": 0xB0C4DE, "Wheel of Fortune": 0xDAA520, "Moon": 0xC0C0C0,
    "Mother": 0x228B22, "Chained": 0x8B0000, "Abyss": 0x000000,
    "Black Emperor": 0x1C1C1C, "Justiciar": 0x4169E1,
}

# ====================== XP CURVES ======================
def get_base_xp_gain(current_seq: int) -> int:
    if current_seq <= 0:
        return 0
    base = random.randint(12, 28)
    multiplier = max(0.35, (current_seq / 9.0) ** 0.78)
    return max(5, int(base * multiplier))

def get_xp_required(current_seq: int) -> int:
    req = {9: 10000, 8: 18000, 7: 32000, 6: 42000, 5: 73000, 4: 91000, 3: 108000, 2: 97000, 1: 151000}
    return req.get(current_seq, 200000)

# ====================== DATABASE ======================
async def init_db():
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, pathway TEXT, sequence INT DEFAULT 9, xp INTEGER DEFAULT 0, last_message TIMESTAMP
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS pathway_gods (
            pathway TEXT PRIMARY KEY, god_user_id INTEGER
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS xp_boosts (
            role_id INTEGER PRIMARY KEY, multiplier REAL DEFAULT 1.0
        )""")
        await db.commit()

# ====================== ROLE MANAGEMENT ======================
async def get_or_create_role(guild: discord.Guild, name: str, pathway: str):
    role = discord.utils.get(guild.roles, name=name)
    if role:
        return role
    color = PATHWAY_COLORS.get(pathway, 0xf5c400)
    return await guild.create_role(name=name, color=discord.Color(color), mentionable=True, reason="LOTM Beyonder Sequence role")

async def remove_old_pathway_role(member: discord.Member, pathway: str):
    for role in member.roles:
        if role.name.startswith(f"[{pathway}] Seq ") or role.name.startswith("👑 ["):
            await member.remove_roles(role)

async def assign_sequence_role(member: discord.Member, pathway: str, seq_num: int):
    seq_name = PATHWAYS[pathway][9 - seq_num] if pathway in PATHWAYS else "Unknown"
    role_name = f"[{pathway}] Seq {seq_num} — {seq_name}"
    if seq_num == 0:
        role_name = f"👑 [{pathway}] Sovereign — {seq_name}"
    role = await get_or_create_role(member.guild, role_name, pathway)
    await remove_old_pathway_role(member, pathway)
    await member.add_roles(role)

# ====================== HELPERS ======================
def get_sequence_name(pathway: str, seq_num: int) -> str:
    if pathway not in PATHWAYS or not (0 <= seq_num <= 9):
        return "Unknown"
    return PATHWAYS[pathway][9 - seq_num]

async def get_user_data(user_id: int):
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        async with db.execute("SELECT pathway, sequence, xp FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return {"pathway": row[0], "sequence": row[1], "xp": row[2]} if row else None

async def update_user(user_id: int, pathway=None, sequence=None, xp=None):
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        if pathway:
            await db.execute("INSERT OR REPLACE INTO users (user_id, pathway, sequence, xp) VALUES (?, ?, ?, ?)", (user_id, pathway, sequence or 9, xp or 0))
        else:
            await db.execute("UPDATE users SET sequence = ?, xp = ? WHERE user_id = ?", (sequence, xp, user_id))
        await db.commit()

async def get_xp_multiplier(member: discord.Member) -> float:
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        async with db.execute("SELECT role_id, multiplier FROM xp_boosts") as cursor:
            boosts = await cursor.fetchall()
        if not boosts:
            return 1.0
        max_mult = 1.0
        for role_id, mult in boosts:
            if discord.utils.get(member.roles, id=role_id):
                max_mult = max(max_mult, mult)
        return max_mult

async def set_xp_boost(role_id: int, multiplier: float):
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        await db.execute("INSERT OR REPLACE INTO xp_boosts (role_id, multiplier) VALUES (?, ?)", (role_id, multiplier))
        await db.commit()

async def remove_xp_boost(role_id: int):
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        await db.execute("DELETE FROM xp_boosts WHERE role_id = ?", (role_id,))
        await db.commit()

async def get_pathway_god(pathway: str):
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        async with db.execute("SELECT god_user_id FROM pathway_gods WHERE pathway = ?", (pathway,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_pathway_god(pathway: str, user_id: int):
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        await db.execute("INSERT OR REPLACE INTO pathway_gods (pathway, god_user_id) VALUES (?, ?)", (pathway, user_id))
        await db.commit()

async def regress_sequence_ones(pathway: str, guild: discord.Guild):
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE pathway = ? AND sequence = 1", (pathway,)) as cursor:
            rows = await cursor.fetchall()
        for (user_id,) in rows:
            await update_user(user_id, sequence=2, xp=0)
            member = guild.get_member(user_id)
            if member:
                await assign_sequence_role(member, pathway, 2)

# ====================== HTTP PING SERVER (Render compatible) ======================
async def ping_handler(request):
    return web.Response(text="OK - LOTM Beyonder Bot is alive!")

async def start_http_server():
    port = int(os.getenv("PORT", 8080))
    app = web.Application()
    app.router.add_get('/ping', ping_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ HTTP ping server started on port {port}")

# ====================== BOT EVENTS ======================
@bot.event
async def on_ready():
    await init_db()
    print(f"✅ {bot.user} — v4.1 loaded successfully!")
    asyncio.create_task(start_http_server())
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Sync error: {e}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    data = await get_user_data(message.author.id)
    if not data or not data["pathway"]: return
    
    now = datetime.utcnow()
    if data.get("last_message"):
        last = datetime.fromisoformat(data["last_message"])
        if (now - last) < timedelta(seconds=45):
            return
    
    # Apply XP Boost
    boost = await get_xp_multiplier(message.author)
    base_xp = get_base_xp_gain(data["sequence"])
    xp_gain = int(base_xp * boost)
    
    new_xp = data["xp"] + xp_gain
    seq = data["sequence"]
    leveled = False
    old_seq = seq
    
    while new_xp >= get_xp_required(seq) and seq > 0:
        new_xp = 0
        seq -= 1
        leveled = True
    
    if seq == 0 and old_seq == 1:
        existing_god = await get_pathway_god(data["pathway"])
        if existing_god:
            seq = 1
            new_xp = 0
            leveled = False
        else:
            await set_pathway_god(data["pathway"], message.author.id)
            await regress_sequence_ones(data["pathway"], message.guild)
            embed = discord.Embed(title="🌌 A NEW PATHWAY GOD IS BORN!", description=f"**{message.author.mention}** has ascended to **Sequence 0** of the **{data['pathway']} Pathway**!\n\nAll other Sequence 1s have been regressed to Sequence 2.", color=0xf5c400)
            await message.channel.send(embed=embed)
    
    await update_user(message.author.id, sequence=seq, xp=new_xp)
    
    if leveled:
        member = message.guild.get_member(message.author.id)
        if member:
            await assign_sequence_role(member, data["pathway"], seq)
        name = get_sequence_name(data["pathway"], seq)
        embed = discord.Embed(title="🌟 SEQUENCE ADVANCEMENT!", description=f"**{message.author.mention}** has advanced in the **{data['pathway']} Pathway**!\n\n**Sequence {seq}: {name}**", color=0xf5c400)
        await message.channel.send(embed=embed)
    
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        await db.execute("UPDATE users SET last_message = ? WHERE user_id = ?", (now.isoformat(), message.author.id))
        await db.commit()

# ====================== XP BOOST COMMANDS ======================
@bot.tree.command(name="set_xp_boost", description="Admin: Give a role an XP multiplier")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(role="Role to boost", multiplier="Multiplier (e.g. 1.5, 2.0)")
async def set_xp_boost_cmd(interaction: discord.Interaction, role: discord.Role, multiplier: float):
    if multiplier < 1.0:
        await interaction.response.send_message("Multiplier must be ≥ 1.0", ephemeral=True)
        return
    await set_xp_boost(role.id, multiplier)
    await interaction.response.send_message(f"✅ **{role.name}** now receives **{multiplier}x** XP!", ephemeral=False)

@bot.tree.command(name="remove_xp_boost", description="Admin: Remove XP boost from a role")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(role="Role to remove boost from")
async def remove_xp_boost_cmd(interaction: discord.Interaction, role: discord.Role):
    await remove_xp_boost(role.id)
    await interaction.response.send_message(f"✅ Removed XP boost from **{role.name}**.", ephemeral=False)

@bot.tree.command(name="xp_boost_list", description="List all active XP boost roles")
async def xp_boost_list(interaction: discord.Interaction):
    async with aiosqlite.connect("lotm_beyonders.db") as db:
        async with db.execute("SELECT role_id, multiplier FROM xp_boosts") as cursor:
            boosts = await cursor.fetchall()
    if not boosts:
        await interaction.response.send_message("No XP boosts configured.", ephemeral=True)
        return
    desc = "**Active XP Boosts:**\n"
    for role_id, mult in boosts:
        role = interaction.guild.get_role(role_id)
        name = role.name if role else f"ID: {role_id}"
        desc += f"• **{name}** → **{mult}x**\n"
    embed = discord.Embed(title="XP Boost List", description=desc, color=0xf5c400)
    await interaction.response.send_message(embed=embed)

# ====================== OTHER COMMANDS ======================
@bot.tree.command(name="setup_roles", description="Admin: Create all Sequence roles with pathway colors")
@app_commands.default_permissions(administrator=True)
async def setup_roles(interaction: discord.Interaction):
    await interaction.response.defer()
    count = 0
    for pathway, seq_list in PATHWAYS.items():
        for seq in range(9, -1, -1):
            seq_name = seq_list[9 - seq]
            role_name = f"[{pathway}] Seq {seq} — {seq_name}"
            if seq == 0:
                role_name = f"👑 [{pathway}] Sovereign — {seq_name}"
            await get_or_create_role(interaction.guild, role_name, pathway)
            count += 1
    await interaction.followup.send(f"✅ Created/Verified **{count}** LOTM Sequence roles!", ephemeral=True)

@bot.tree.command(name="choose_pathway", description="Choose your Beyonder Pathway")
@app_commands.describe(pathway="Your chosen path")
@app_commands.choices(pathway=[app_commands.Choice(name=p, value=p) for p in sorted(PATHWAYS.keys())])
async def choose_pathway(interaction: discord.Interaction, pathway: str):
    await update_user(interaction.user.id, pathway=pathway, sequence=9, xp=0)
    member = interaction.guild.get_member(interaction.user.id)
    if member:
        await assign_sequence_role(member, pathway, 9)
    name = get_sequence_name(pathway, 9)
    embed = discord.Embed(title="🔥 YOU HAVE CHOSEN!", description=f"**{interaction.user.mention}** is now **Sequence 9: {name}** of the **{pathway} Pathway**!", color=0x4a0e4a)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="profile", description="View your Beyonder profile")
async def profile(interaction: discord.Interaction):
    data = await get_user_data(interaction.user.id)
    if not data or not data["pathway"]:
        await interaction.response.send_message("Use `/choose_pathway` first!", ephemeral=True)
        return
    seq = data["sequence"]
    name = get_sequence_name(data["pathway"], seq)
    progress = data["xp"]
    needed = get_xp_required(seq)
    percent = min(int((progress / needed) * 100), 100) if needed else 100
    title = "👑 PATHWAY SOVEREIGN" if seq == 0 else "📜 BEYONDER PROFILE"
    embed = discord.Embed(title=title, color=0xf5c400)
    embed.add_field(name="Pathway", value=data["pathway"], inline=True)
    embed.add_field(name="Sequence", value=f"{seq} — {name}", inline=True)
    embed.add_field(name="Progress", value=f"{progress}/{needed} XP ({percent}%) — resets on level up", inline=False)
    await interaction.response.send_message(embed=embed)

# ====================== PROPER ASYNC MAIN ======================
async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN environment variable is not set!")
        return
    print("Starting bot...")
    await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped manually.")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import asyncio
asyncio.get_event_loop().run_until_complete(main())
