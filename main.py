import io
import discord
import requests_async as requests
import json
import datetime

intents = discord.Intents(messages=True, guilds=True)
bot = discord.Bot(intents=intents)

token = "Here goes your token"
apiUrl = "http://localhost:11434/"

@bot.command(description="List currently installed models")
async def versions(ctx: discord.commands.ApplicationContext):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    responseFromAPI = await requests.get(apiUrl + 'api/tags', headers=headers)

    response = ""
    for model in json.loads(responseFromAPI.content)["models"]:
        response += model["name"] + " \n"

    await ctx.respond(response, ephemeral=True)

async def sendPossiblyLongMessage(channel: discord.channel, textMessage: str):
    if(len(textMessage) >= 2000):
        textBuffer = io.BytesIO(bytes(textMessage, "utf-8"))
        await channel.send(file=discord.File(textBuffer, "response.txt"))
        return
    await channel.send(textMessage)

async def callModelAPI(messageHist: list, model) -> str:
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {"model":  model,
            "messages": messageHist,
            "stream": False,
            }

    responseFromAPI = await requests.post(apiUrl + 'api/chat', headers=headers, data=json.dumps(data))

    return json.loads(responseFromAPI.content)["message"]["content"]

versionCompletionData = {}

#this could have been handled better
async def modelVersionCompletion(ctx: discord.AutocompleteContext):

    #bootstrap
    if(len(versionCompletionData) == 0):
        versionCompletionData["time"] = datetime.datetime.now()
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        responseFromAPI = await requests.get(apiUrl + 'api/tags', headers=headers)
        models = []
        for model in json.loads(responseFromAPI.content)["models"]:
            models.append(model["name"])
        versionCompletionData["models"] = models
        return models

    #5 minute cache so i dont spam api
    if((datetime.datetime.now() - versionCompletionData["time"]).total_seconds() * 60 >= 5):
        versionCompletionData["time"] = datetime.datetime.now()
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        responseFromAPI = await requests.get(apiUrl + 'api/tags', headers=headers)
        models = []
        for model in json.loads(responseFromAPI.content)["models"]:
            models.append(model["name"])
        versionCompletionData["models"] = models
        return models

    return versionCompletionData["models"]

@bot.command(description="Create thread channel to message LLM")
async def chat(ctx: discord.commands.ApplicationContext,
               model: discord.Option(discord.SlashCommandOptionType.string, description="Choose your model e.g llama3.1", autocomplete=discord.utils.basic_autocomplete(modelVersionCompletion)),
               prompt: discord.Option(discord.SlashCommandOptionType.string, description="Tell it what to do, prompt", max_length=6000),
               threadname:  discord.Option(discord.SlashCommandOptionType.string, description="Thread name e.g testing a prompt", max_length=100),
               system: discord.Option(discord.SlashCommandOptionType.string, description="System prompt, example You are an assistant and respond like pirate", max_length=6000)="",
               ):

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    responseFromAPI = await requests.get(apiUrl + 'api/tags', headers=headers)

    matches = False
    for modelCheck in json.loads(responseFromAPI.content)["models"]:
        if(modelCheck["name"] == model):
            matches = True

    if(not matches):
        await ctx.respond("You try to use model that is not installed on the server please use /versions command and select correct model",  ephemeral=True)
        return


    await ctx.respond("Creating thread channel please wait...", ephemeral=True)
    message = await ctx.send(f"""<@{ctx.author.id}> \n{model}:{prompt}""")
    thread = await message.create_thread(name=threadname, auto_archive_duration=10080)
    await thread.send(f"""System; {system} \nstart; {prompt}\nmodel; {model}; \nMessages with - at beggining are skipped by bot, this might change in future""")

    builder = []
    if(system != ""):
        builder.append({"role": "system", "content": str(system)})
    builder.append({"role": "user", "content": str(prompt)})
    await sendPossiblyLongMessage(thread, await callModelAPI(builder, model))

@bot.command(description="Does a prompt for all models") # this decorator makes a slash command
async def allmodels(ctx: discord.commands.ApplicationContext,
               prompt: discord.Option(discord.SlashCommandOptionType.string, description="Tell it what to do, prompt", max_length=6000),
               threadname: discord.Option(discord.SlashCommandOptionType.string, description="Thread name e.g testing a prompt", max_length=100),
               system: discord.Option(discord.SlashCommandOptionType.string, description="System prompt, example You are an assistant and respond like pirate", max_length=6000)="",
               ):

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    responseFromAPI = await requests.get(apiUrl + 'api/tags', headers=headers)

    await ctx.respond("Creating thread channels for all available models...", ephemeral=True)

    for model in json.loads(responseFromAPI.content)["models"]:
        modelName = model["name"]

        message = await ctx.send(f"""<@{ctx.author.id}> \n{modelName}:{prompt}""")
        thread = await message.create_thread(name=threadname, auto_archive_duration=10080)
        await thread.send(f"""System; {system} \nstart; {prompt}\nmodel; {modelName}; \nMessages with - at beggining are skipped by bot, this might change in future""")

        builder = []
        if(system != ""):
            builder.append({"role": "system", "content": str(system)})
        builder.append({"role": "user", "content": str(prompt)})
        await sendPossiblyLongMessage(thread, await callModelAPI(builder, modelName))

@bot.event
async def on_message(currentMessage: discord.Message):
    if(currentMessage.author.id == bot.application_id):
        return

    if(currentMessage.channel.type != discord.enums.ChannelType.public_thread):
        return

    if(currentMessage.channel.owner_id != bot.application_id):
        return

    #this will contain messages that will be forwarded to llm
    messageHistory = []


    #tldr for some reason first message is empty
    #so i use second message for inital prompt
    messagesInThread = []
    async for x in currentMessage.channel.history(oldest_first=True, limit=9999):
        messagesInThread.append(x)


    initialMessage = messagesInThread[1].content
    splited = initialMessage.split("\n")
    system = splited[0].split(";")[1].strip()
    user = splited[1].split(";")[1].strip()
    model = splited[2].split(";")[1].strip()

    # system can be empty == default behaviour
    if(system != ""):
        messageHistory.append({"role": "system", "content": str(system)})
    messageHistory.append({"role": "user", "content": str(user)})

    if(messagesInThread[-1].content.startswith("-")):
        return

    for message in messagesInThread[2:]:
        content = None

        #Skip messages with - at beggining
        if(message.content.startswith("-")):
            continue

        if(message.attachments):
            for attachment in message.attachments:
                if(".txt" in attachment.filename):
                    attachmentBuffer = await attachment.read(use_cached=False)
                    content = str(attachmentBuffer, "utf-8")
        else:
            content = message.content

        if (content == None):
            await currentMessage.reply(
                "You send an attachment which overrides message content and it's not .txt remove it, and this message")
            break


        if(message.author.id == bot.application_id):
            messageHistory.append({"role": "assistant", "content": content})
        else:
            messageHistory.append({"role": "user", "content": content})
    print(f"Calling model for message {currentMessage.id}: {model}")
    llmResponse = await callModelAPI(messageHistory, model)
    await sendPossiblyLongMessage(currentMessage.channel, llmResponse)

if __name__=="__main__":
    bot.run(token)

