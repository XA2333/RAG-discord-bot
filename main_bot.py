import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from backend.rag_pipeline import RAGPipeline
from backend.ingestion_service import IngestionService
from backend.mongo_store import MongoVectorStore

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

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
        embed.add_field(name="!ask <question>", value="Ask a question based on the documents.", inline=False)
        embed.add_field(name="!upload", value="Attach a PDF file to this command to upload it.", inline=False)
        embed.add_field(name="!delete <filename>", value="Delete a document by its filename.", inline=False)
        embed.add_field(name="!list", value="List all available documents.", inline=False)
        embed.add_field(name="Mention Me", value="@Bot <question> works just like !ask", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    global rag_pipeline, ingest_service, mongo_store
    print(f'Logged in as {bot.user}')
    try:
        rag_pipeline = RAGPipeline()
        ingest_service = IngestionService()
        mongo_store = MongoVectorStore()
        print("Services Initialized.")
    except Exception as e:
        print(f"Failed to init services: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Handle Mentions
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        question = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if question:
            ctx = await bot.get_context(message)
            await ask(ctx, question=question)
            return

    await bot.process_commands(message)

@bot.command(name='help')
async def help_command(ctx):
    view = HelpView()
    await ctx.send("Click below to see what I can do!", view=view)

@bot.command(name='ask')
async def ask(ctx, *, question):
    if not rag_pipeline:
        await ctx.send("⚠️ Bot is warming up.")
        return

    async with ctx.typing():
        response = await bot.loop.run_in_executor(None, rag_pipeline.answer_question, question)
    
    # Chunk long responses
    if len(response) > 2000:
        for i in range(0, len(response), 2000):
            await ctx.send(response[i:i+2000])
    else:
        await ctx.send(response)

@bot.command(name='upload')
async def upload(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach a PDF file to upload.")
        return

    attachment = ctx.message.attachments[0]
    if not attachment.filename.lower().endswith(".pdf"):
        await ctx.send("❌ Only PDF files are supported.")
        return

    msg = await ctx.send(f"📥 Downloading `{attachment.filename}`...")
    
    try:
        file_bytes = await attachment.read()
        
        # Run ingestion in executor
        num_chunks = await bot.loop.run_in_executor(
            None, 
            ingest_service.process_file_bytes, 
            file_bytes, 
            attachment.filename
        )
        await msg.edit(content=f"✅ Successfully ingested `{attachment.filename}` ({num_chunks} chunks).")
    
    except Exception as e:
        await msg.edit(content=f"❌ Ingestion failed: {str(e)}")

@bot.command(name='delete')
async def delete(ctx, filename: str):
    msg = await ctx.send(f"🗑️ Deleting `{filename}`...")
    try:
        # Run delete in executor
        count = await bot.loop.run_in_executor(None, mongo_store.delete_document, filename)
        if count > 0:
            await msg.edit(content=f"✅ Deleted `{filename}` ({count} chunks removed).")
        else:
            await msg.edit(content=f"⚠️ File `{filename}` not found in database.")
    except Exception as e:
        await msg.edit(content=f"❌ Delete failed: {str(e)}")

@bot.command(name='list')
async def list_docs(ctx):
    try:
        docs = await bot.loop.run_in_executor(None, mongo_store.list_documents)
        if docs:
            doc_list = "\n".join([f"- `{d}`" for d in docs])
            await ctx.send(f"📂 **Available Documents:**\n{doc_list}")
        else:
            await ctx.send("📂 Database is empty.")
    except Exception as e:
        await ctx.send(f"❌ Error listing documents: {str(e)}")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN missing.")
        exit(1)
    bot.run(TOKEN)
