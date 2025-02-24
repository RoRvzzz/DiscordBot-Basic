import nextcord
from nextcord.ext import commands
import sqlite3

TOKEN = 'YOUR_BOT_TOKEN' # using environmental variables are much better for simplicity the token is hardcoded
intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

conn = sqlite3.connect('economy.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS balances (
        user_id TEXT PRIMARY KEY,
        balance INTEGER
    )
''')
conn.commit()

def get_balance(user_id):
    cursor.execute('SELECT balance FROM balances WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute('INSERT INTO balances (user_id, balance) VALUES (?, ?)', (user_id, 0))
        conn.commit()
        return 0
    return result[0]

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=nextcord.Game(name="with commands | !cmds"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the required permissions to run this command. | ❌")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Bad argument provided. Please check your command. | ⚠️")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param} | ⚠️")
    else:
        await ctx.send(f"An error occurred: {error} | ❗")

@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! | Latency: {latency}ms | 🏓')

@bot.command(name='work')
async def work(ctx):
    user_id = str(ctx.author.id)
    balance = get_balance(user_id)
    earnings = 10
    balance += earnings
    cursor.execute('UPDATE balances SET balance = ? WHERE user_id = ?', (balance, user_id))
    conn.commit()
    await ctx.send(f'{ctx.author.mention}, you worked hard and earned {earnings} tokens! | Your balance is now {balance} tokens. | 💼')

@bot.command(name='bal')
async def balance(ctx, user: nextcord.User = None):
    user = user or ctx.author
    user_id = str(user.id)
    balance = get_balance(user_id)
    await ctx.send(f'{user.mention}, your balance is {balance} tokens. | 💰')

@bot.command(name='withdraw')
async def withdraw(ctx, amount: int):
    user_id = str(ctx.author.id)
    balance = get_balance(user_id)

    if amount <= 0:
        await ctx.send(f'{ctx.author.mention}, please provide a valid positive amount. | ⚠️')
    elif amount > balance:
        await ctx.send(f'{ctx.author.mention}, insufficient funds. | ❌')
    else:
        balance -= amount
        cursor.execute('UPDATE balances SET balance = ? WHERE user_id = ?', (balance, user_id))
        conn.commit()
        await ctx.send(f'{ctx.author.mention}, you withdrew {amount} tokens. | Your balance is now {balance} tokens. | 🏦')

@bot.command(name='pay')
async def pay(ctx, user: nextcord.User, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(user.id)

    sender_balance = get_balance(sender_id)
    receiver_balance = get_balance(receiver_id)

    if amount <= 0 or amount > sender_balance:
        await ctx.send(f'{ctx.author.mention}, invalid amount or insufficient funds. | ❌')
    else:
        sender_balance -= amount
        receiver_balance += amount
        cursor.execute('UPDATE balances SET balance = ? WHERE user_id = ?', (sender_balance, sender_id))
        cursor.execute('UPDATE balances SET balance = ? WHERE user_id = ?', (receiver_balance, receiver_id))
        conn.commit()
        await ctx.send(f'{ctx.author.mention}, you paid {user.mention} {amount} tokens. | Your balance is now {sender_balance} tokens. | 💸')

@bot.command(name='leaderboard')
async def leaderboard(ctx):
    cursor.execute('SELECT user_id, balance FROM balances ORDER BY balance DESC LIMIT 10')
    top_users = cursor.fetchall()
    leaderboard_message = '\n'.join([f'<@{user_id}> | {balance} tokens | 🏆' for user_id, balance in top_users])
    await ctx.send(f'**Leaderboard** | 📜\n{leaderboard_message}')

bot.run(TOKEN)
