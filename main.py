import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from rag.pipeline import answer_question

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Connected to {len(bot.guilds)} guilds')

@bot.command(name='ask')
async def ask(ctx, *, question):
    await ctx.send(f"Thinking about: {question}...")
    try:
        # Running non-async blocking code in executor to avoid freezing bot
        response = await bot.loop.run_in_executor(None, answer_question, question)
        # Discord has a 2000 char limit, splitting if necessary
        if len(response) > 2000:
            for i in range(0, len(response), 2000):
                await ctx.send(response[i:i+2000])
        else:
            await ctx.send(response)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Process commands first
    await bot.process_commands(message)

if __name__ == "__main__":
    if not TOKEN or "your_" in TOKEN:
        print("Error: DISCORD_TOKEN is not set in .env")
    else:
        bot.run(TOKEN)
