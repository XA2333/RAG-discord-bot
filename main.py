import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from backend.rag_pipeline import RAGService
from backend.azure_client import AzureAIClient

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Startup Check
print("--- STARTUP CHECK ---")
try:
    print("1. Testing Azure Connection...")
    client = AzureAIClient()
    vec = client.generate_embedding("ping")
    print(f"   [OK] Azure Connectivity (Dim: {len(vec)})")
except Exception as e:
    print(f"   [FAIL] Azure Error: {e}")
    exit(1)

print("2. Initializing RAG Service...")
try:
    rag_service = RAGService()
    print("   [OK] RAG Service Ready")
except Exception as e:
    print(f"   [FAIL] RAG Init Error: {e}")
    exit(1)
print("---------------------")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command(name='ask')
async def ask(ctx, *, question):
    await ctx.send(f"🔍 **Searching:** {question}...")
    try:
        # Run blocking RAG logic in executor
        response = await bot.loop.run_in_executor(None, rag_service.answer_question, question)
        
        # Split fit Discord 2000 char limit
        if len(response) > 2000:
            for i in range(0, len(response), 2000):
                await ctx.send(response[i:i+2000])
        else:
            await ctx.send(response)
    except Exception as e:
        await ctx.send(f"❌ **Error:** {str(e)}")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN is missing in .env")
    else:
        bot.run(TOKEN)
