from dotenv import load_dotenv
import os
import discord
from discord import app_commands


# reads variables from a .env file and sets them in os.environ
load_dotenv()  
#Carga de token, conexión con la API de Discord
token = os.getenv("DISCORD_TOKEN")  
# configuración sobre qué categorías de eventos recibiremos.
intents=discord.Intents.default()
#cliente que utilizará esa configuración para manejar conexión con Discord.
client = discord.Client(intents=intents)



#   -------------------------------------------------------#
#                          COMANDOS                        #
#   -------------------------------------------------------#

tree = app_commands.CommandTree(client)

@tree.command(name="ping", description="Initial message'")  # comando de barra
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        "I'm the grandmaster of Gusu Lan"
    ) # respuesta al comando    
    
    
    
    
    
#   -------------------------------------------------------#
#                    CONEXIÓN CON DISCORD                  #
#   -------------------------------------------------------#

@client.event
async def on_ready():
    guild = discord.Object(id=1540358191387513034)

    tree.copy_global_to(guild=guild)
    synced = await tree.sync(guild=guild)

    print(f"Synced commands: {len(synced)}")
    print("Bot ready for use")

client.run(token)