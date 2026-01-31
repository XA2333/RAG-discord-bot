import os
import io
import discord
from discord.ext import commands
from dotenv import load_dotenv
from backend.rag_pipeline import RAGPipeline
from backend.ingestion_service import IngestionService
from backend.mongo_store import MongoVectorStore

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Globals
rag_pipeline = None
ingest_service = None
mongo_store = None

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Show Commands", style=discord.ButtonStyle.primary, emoji="📜")
    async def show_commands(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🤖 RAG Bot Commands", color=discord.Color.blue())
        embed.add_field(name="!ask <question> / @Bot", value="Ask a question based on uploaded docs.", inline=False)
        embed.add_field(name="!upload", value="[Admin] Attach a PDF to upload.", inline=False)
        embed.add_field(name="!delete <filename>", value="[Admin] Delete a document.", inline=False)
        embed.add_field(name="!sources", value="List available documents.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    global rag_pipeline, ingest_service, mongo_store
    print(f'Logged in as {bot.user}')
    try:
        rag_pipeline = RAGPipeline()
        ingest_service = IngestionService()
        mongo_store = MongoVectorStore()
        print("Backend Services Initialized.")
    except Exception as e:
        print(f"Failed to init services: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Handle @Mentions
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        content = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if content:
            # Route to !ask logic
            await _handle_ask(message.channel, content, message.author.id)
            return

    await bot.process_commands(message)

async def _handle_ask(channel, question, user_id=None):
    if not rag_pipeline:
        await channel.send("⚠️ Bot is warming up.")
        return

    async with channel.typing():
        response = await bot.loop.run_in_executor(None, rag_pipeline.answer_question, question, user_id)
    
    if len(response) > 2000:
        for i in range(0, len(response), 2000):
            await channel.send(response[i:i+2000])
    else:
        await channel.send(response)

@bot.command(name='ask')
async def ask(ctx, *, question):
    await _handle_ask(ctx.channel, question, ctx.author.id)

@bot.command(name='help')
async def help_command(ctx):
    embed = discord.Embed(title="RAG Bot", description="Click below to see commands.", color=discord.Color.gold())
    view = HelpView()
    await ctx.send(embed=embed, view=view)

@bot.command(name='upload')
async def upload(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach a PDF file.")
        return

    attachment = ctx.message.attachments[0]
    if not attachment.filename.lower().endswith(".pdf"):
        await ctx.send("❌ Only PDF files are supported.")
        return
    
    if attachment.size > MAX_UPLOAD_MB * 1024 * 1024:
        await ctx.send(f"❌ File too large. Max size is {MAX_UPLOAD_MB}MB.")
        return

    status_msg = await ctx.send(f"📥 Downloading `{attachment.filename}`...")
    
    try:
        file_bytes = await attachment.read()
        file_stream = io.BytesIO(file_bytes)
        
        # Generator for progress updates
        # Must run blocking generator in a way that doesn't block loop?
        # Ideally we iterate over the generator in the main loop, 
        # but the generator does blocking network calls.
        # Solution: Run the whole process in executor and have it return full string or handle async stream?
        # For simplicity in discord.py 2.0, we can accept blocking for short batches or use asyncio.to_thread on each step.
        # We'll use a wrapper to run the generator fully.
        
        def run_ingest():
            logs = []
            for status in ingest_service.process_stream(file_stream, attachment.filename):
                logs.append(status)
            return logs

        logs = await bot.loop.run_in_executor(None, run_ingest)
        
        final_status = logs[-1] if logs else "Done."
        await status_msg.edit(content=f"✅ **Ingestion Complete**\n`{attachment.filename}`\n{final_status}")

    except Exception as e:
        await status_msg.edit(content=f"❌ Ingestion Failed: {str(e)}")

@bot.command(name='delete')
async def delete(ctx, filename: str):
    msg = await ctx.send(f"🗑️ Deleting `{filename}`...")
    try:
        count = await bot.loop.run_in_executor(None, mongo_store.delete_by_source, filename)
        if count > 0:
            await msg.edit(content=f"✅ Deleted `{filename}` ({count} chunks removed).")
        else:
            await msg.edit(content=f"⚠️ File `{filename}` not found.")
    except Exception as e:
        await msg.edit(content=f"❌ Delete failed: {e}")

@bot.command(name='sources')
async def sources(ctx):
    try:
        srcs = await bot.loop.run_in_executor(None, mongo_store.list_sources)
        if srcs:
            formatted = "\n".join([f"- `{s}`" for s in srcs])
            await ctx.send(f"📂 **Knowledge Base:**\n{formatted}")
        else:
            await ctx.send("📂 Knowledge Base is empty.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❓ Unknown command. Type `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing argument: `{error.param.name}`. Please check the command format.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ You do not have permission to run this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"⚠️ Invalid argument: {str(error)}")
    else:
        await ctx.send(f"❌ Error: {str(error)}")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN missing.")
        exit(1)
    bot.run(TOKEN)
