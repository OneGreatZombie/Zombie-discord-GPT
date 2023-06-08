from discord.ext import commands
import discord
import openai

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

bot_token = "Discord Bot Token"
gpt_api_key = "Open AI Key"

openai.api_key = gpt_api_key

gpt_enabled = {}  # Dictionary to store the activation status per agent
memory_storage = {}  # Dictionary to store previous chat messages per agent

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")

@bot.event
async def on_message(message):
    global memory_storage

    if message.author == bot.user:
        return

    user_id = str(message.author.id)

    if user_id not in memory_storage:
        memory_storage[user_id] = []

    if gpt_enabled.get(user_id, False):
        memory_storage[user_id].append(message.content)  # Store the message in memory

        # Merge previous chats into the user input
        user_input = f"{message.content}\n\nPrevious Chats:\n{format_memory(memory_storage[user_id])}"

        gpt_response = generate_gpt_response(user_input)
        memory_storage[user_id].append(gpt_response)  # Store the AI response in memory
        await message.channel.send(gpt_response)

    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
async def activate(ctx, agent_name: str):
    global gpt_enabled
    user_id = str(ctx.author.id)

    if agent_name.lower() == "zombie":
        gpt_enabled[user_id] = True
        await ctx.send("GPT response activated for Zombie agent.")
    else:
        await ctx.send("Invalid agent name.")

@bot.command()
async def disable(ctx, agent_name: str):
    global gpt_enabled
    user_id = str(ctx.author.id)

    if agent_name.lower() == "zombie":
        gpt_enabled[user_id] = False
        await ctx.send("GPT response disabled for Zombie agent.")
    else:
        await ctx.send("Invalid agent name.")

@bot.command()
async def recall(ctx):
    global memory_storage
    user_id = str(ctx.author.id)
    if user_id in memory_storage:
        previous_chats = "\n".join(memory_storage[user_id])
        await ctx.send(f"Previous Chats:\n{previous_chats}")
    else:
        await ctx.send("No previous chats found.")

def generate_gpt_response(user_input):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=user_input,
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.7
    )

    gpt_response = response.choices[0].text.strip()

    # Check if the response contains code
    if "code" in gpt_response:
        # Extract the code from the response
        code_start_index = gpt_response.find("```")
        code_end_index = gpt_response.rfind("```")
        if code_start_index != -1 and code_end_index != -1:
            code = gpt_response[code_start_index + 3:code_end_index].strip()
            code_language = "python"  # Set the default code language to Python (you can modify this if needed)
            formatted_code = f"```{code_language}\n{code}\n```"

            # Replace the code in the response with the formatted code
            gpt_response = gpt_response[:code_start_index] + formatted_code + gpt_response[code_end_index + 3:]

    return gpt_response

def format_memory(memory_storage):
    # Convert previous chat messages into a formatted string
    formatted_chats = ""
    for chat in memory_storage:
        if chat.startswith("```") and chat.endswith("```"):
            formatted_chats += chat  # Preserve code blocks as is
        else:
            formatted_chats += f"> {chat}\n"

    return formatted_chats

bot.run(bot_token)
