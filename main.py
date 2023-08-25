TOKEN = ""

import nextcord, sqlite3
db=sqlite3.connect('db.db')
sql = db.cursor()
sql.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT,
    current_channel BIGINT,
    name TEXT,
    vlimit BIGINT
)""")
sql.execute("""CREATE TABLE IF NOT EXISTS servers (
    server_id BIGINT,
    category BIGINT,
    channel BIGINT
)""")

db.commit()
from nextcord.ext import commands
bot = commands.Bot(command_prefix="!", intents=nextcord.Intents().all())
def check(ids, name):
    sql.execute(f"SELECT * FROM users WHERE user_id = {ids}")
    if sql.fetchone() is None:
        sql.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (ids, 0, name, 0))
@bot.event
async def on_guild_join(guild):
    sql.execute("INSERT INTO servers VALUES (?, ?, ?)", (guild.id, 0, 0))
    db.commit()
@bot.command()
async def setup(ctx):
    msg=await ctx.send(">>> Процесс..")
    import time
    from datetime import timedelta
    start_time = time.monotonic()
    
    cat=await ctx.guild.create_category(name="Private Channels")
    j=await cat.create_voice_channel("[+] Join to create")
    sql.execute(f"UPDATE servers SET category = {cat.id} WHERE server_id = {ctx.guild.id}")
    sql.execute(f"UPDATE servers SET channel = {j.id} WHERE server_id = {ctx.guild.id}")
    
    db.commit()
    end_time = time.monotonic()
    await msg.edit(content=f">>> Каналы и категории созданы за `{end_time - start_time} сек`!")
    
@bot.command()
async def name(ctx, *, name):
    check(ctx.author.id, ctx.author.name)
    
    await ctx.send(f">>> Имя канала теперь `{name}`")
    
    sql.execute(f"UPDATE users SET name = '{name}' WHERE user_id = {ctx.author.id}")
    db.commit()
    
    for x in sql.execute(f"SELECT * FROM users WHERE user_id = {ctx.author.id}"):
        if x[1] != 0:
            try:
                ch = bot.get_channel(x[1])
                await ch.edit(name=name)
            except: pass
@bot.command()
async def limit(ctx, limit=0):
    check(ctx.author.id, ctx.author.name)
    
    if limit == 0: await ctx.send(f">>> Лимит канала теперь `неограничего`")
    else: await ctx.send(f">>> Лимит канала теперь `{limit}`")
    
    sql.execute(f"UPDATE users SET vlimit = '{limit}' WHERE user_id = {ctx.author.id}")
    db.commit()
    
    for x in sql.execute(f"SELECT * FROM users WHERE user_id = {ctx.author.id}"):
        if x[1] != 0:
            try:
                ch = bot.get_channel(x[1])
                await ch.edit(user_limit=limit)
            except: pass
@bot.event
async def on_voice_state_update(member, before, after):
    print("y")
    if not before.channel and after.channel:
        for x in sql.execute(f"SELECT * FROM users WHERE user_id = {member.id}"):
            if x[2]==0 or after.channel.id != x[2]: return
        
        check(member.id, member.name)
        
        for x in sql.execute(f"SELECT * FROM users WHERE user_id = {member.id}"):
            if x[3] == 0: ch=await member.guild.create_voice_channel(x[2])
            else: ch=await member.guild.create_voice_channel(x[2], user_limit=x[3])
            
            sql.execute(f"UPDATE users SET current_channel = {ch.id} WHERE user_id = {member.id}")
            db.commit()
            await member.move_to(ch)
    if not after.channel and before.channel:
        for x in sql.execute(f"SELECT * FROM users WHERE current_channel = {before.channel.id}"):
            if member.id==x[0]:
                await before.channel.delete()
                
                sql.execute(f"UPDATE users SET current_channel = 0 WHERE user_id = {member.id}")
                db.commit()
    

bot.run(TOKEN)
