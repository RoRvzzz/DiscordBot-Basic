import nextcord
from nextcord.ext import commands
import sqlite3

# To Do:
# Start using cogs - organize code better
# Add the Roblox API connection - Need API key
# All code work first try - Impossible
# Sqlite3 DB - DONE!
# and make f'{prefix}status command - !ping needs update

TOKEN = 'YOUR_BOT_TOKEN'
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

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=nextcord.Game(name="with commands | !cmds"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        original_error = error.original
        await handle_errors(ctx, original_error)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the required permissions to run this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Bad argument provided. Please check your command.")
    elif isinstance(error, commands.Forbidden):
        await ctx.send("Forbidden: Missing Permissions")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param}")
    else:
        await ctx.send(f"An error occurred: {error}")

async def handle_errors(ctx, error):
    if isinstance(error, nextcord.errors.NotFound):
        await ctx.send("Error: User not found.")
    else:
        await ctx.send(f"An error occurred: {error}")

@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)  
    await ctx.send(f'Pong! Latency: {latency}ms')

@bot.command(name='work')
async def work(ctx):
    user_id = str(ctx.author.id)
    cursor.execute('SELECT balance FROM balances WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result is None:
        cursor.execute('INSERT INTO balances (user_id, balance) VALUES (?, ?)', (user_id, 0))
        conn.commit()
        balance = 0
    else:
        balance = result[0]

    earnings = 10  
    balance += earnings
    cursor.execute('UPDATE balances SET balance = ? WHERE user_id = ?', (balance, user_id))
    conn.commit()
    await ctx.send(f'{ctx.author.mention}, you worked hard and earned {earnings} tokens! Your balance is now {balance} tokens.')

@bot.command(name='bal')
async def balance(ctx):
    user_id = str(ctx.author.id)
    cursor.execute('SELECT balance FROM balances WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result is None:
        cursor.execute('INSERT INTO balances (user_id, balance) VALUES (?, ?)', (user_id, 0))
        conn.commit()
        balance = 0
    else:
        balance = result[0]

    await ctx.send(f'{ctx.author.mention}, your balance is {balance} tokens.')

@bot.command(name='withdraw')
async def withdraw(ctx, amount: int):
    user_id = str(ctx.author.id)
    cursor.execute('SELECT balance FROM balances WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result is None:
        cursor.execute('INSERT INTO balances (user_id, balance) VALUES (?, ?)', (user_id, 0))
        conn.commit()
        balance = 0
    else:
        balance = result[0]

    if amount <= 0:
        await ctx.send(f'{ctx.author.mention}, please provide a valid positive amount.')
    elif amount > balance:
        await ctx.send(f'{ctx.author.mention}, invalid amount or insufficient funds.')
    else:
        balance -= amount
        cursor.execute('UPDATE balances SET balance = ? WHERE user_id = ?', (balance, user_id))
        conn.commit()
        await ctx.send(f'{ctx.author.mention}, you withdrew {amount} tokens. Your balance is now {balance} tokens.')

@bot.command(name='pay')
async def pay(ctx, user: nextcord.User, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(user.id)

    # note Check sender's balance
    cursor.execute('SELECT balance FROM balances WHERE user_id = ?', (sender_id,))
    sender_result = cursor.fetchone()

    if sender_result is None:
        cursor.execute('INSERT INTO balances (user_id, balance) VALUES (?, ?)', (sender_id, 0))
        conn.commit()
        sender_balance = 0
    else:
        sender_balance = sender_result[0]

    # note Check receiver's balance
    cursor.execute('SELECT balance FROM balances WHERE user_id = ?', (receiver_id,))
    receiver_result = cursor.fetchone()

    if receiver_result is None:
        cursor.execute('INSERT INTO balances (user_id, balance) VALUES (?, ?)', (receiver_id, 0))
        conn.commit()
        receiver_balance = 0
    else:
        receiver_balance = receiver_result[0]

    if amount <= 0 or amount > sender_balance:
        await ctx.send(f'{ctx.author.mention}, invalid amount or insufficient funds.')
    else:
        sender_balance -= amount
        receiver_balance += amount
        cursor.execute('UPDATE balances SET balance = ? WHERE user_id = ?', (sender_balance, sender_id))
        cursor.execute('UPDATE balances SET balance = ? WHERE user_id = ?', (receiver_balance, receiver_id))
        conn.commit()
        await ctx.send(f'{ctx.author.mention}, you paid {user.mention} {amount} tokens. Your balance is now {sender_balance} tokens.')

@bot.command(name='prefix')
async def change_prefix(ctx, new_prefix):
    # note Check if the user has the "manage_guild" permission
    if ctx.author.guild_permissions.manage_guild:
        bot.command_prefix = new_prefix
        bot.prefix_variable = new_prefix 
        await ctx.send(f'Prefix set to: {new_prefix}')
    else:
        await ctx.send("You don't have the required permissions to change the prefix.")

@bot.command(name='cmds')
async def show_commands(ctx):
    # note Display the stored prefix
    prefix = bot.prefix_variable if hasattr(bot, 'prefix_variable') else '!'
    commands_list = [
        f'{prefix}ping - Check bot latency.',
        f'{prefix}kick <member> [reason] - Kick a member from the server (requires kick_members permission).',
        f'{prefix}ban <member> [reason] - Ban a member from the server (requires ban_members permission).',
        f'{prefix}clear [amount] - Clear a certain number of messages in the channel (requires manage_messages permission).',
        f'{prefix}announce <channel> <message> - Make an embedded announcement to the specified channel.',
        f'{prefix}reactionroles - Display the',
        f'{prefix}suggest <suggestion> - Make a suggestion.',
        f'{prefix}suggestion channel <channel_id> - Change the suggestion channel.',
        f'{prefix}prefix <new_prefix> - Set the bot\'s prefix (requires manage_guild permission).',
        f'{prefix}cmds - Show a list of all commands and their descriptions.',
        f'{prefix}userinfo [member] - Get information about a user.',
        f'{prefix}serverinfo - Get information about the server.',
        f'{prefix}poll <question> [option1] [option2]... - Create a poll.',
        f'{prefix}activity <activity> - Set the bot\'s activity status.',
        f'{prefix}work - Earn tokens by working.',
        f'{prefix}bal - Check your token balance.',
        f'{prefix}withdraw <amount> - Withdraw tokens from your account.',
        f'{prefix}pay <user> <amount> - Pay tokens to another user.',
    ]
    await ctx.send('\n'.join(commands_list))

bot.run(TOKEN)
