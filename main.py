from dotenv import load_dotenv
import os
import discord


#-------------------------------------------------------#
#              LOAD ENVIRONMENT VARIABLES               #
#-------------------------------------------------------#

load_dotenv()  # reads variables from a .env file and sets them in os.environ

#Carga de token, conexión con la API de Discord
token = os.getenv("DISCORD_TOKEN")

#-------------------------------------------------------#
#                       CLIENT DISCORD                  #
#-------------------------------------------------------#

# configuración sobre qué categorías de eventos recibiremos.
intents=discord.Intents.default()

#cliente que utilizará esa configuración para manejar conexión con Discord.
client = discord.Client(intents=intents)


#   -------------------------------------------------------#
#                     EVENTOS DEL CLIENTE                  #
#   -------------------------------------------------------#

def online():
    print("Bot ready for use")
    

@client.event
async def on_ready():
    online()
    
    
    
#   -------------------------------------------------------#
#                    CONEXIÓN CON DISCORD                  #
#   -------------------------------------------------------#

client.run(token)  # inicia la conexión con Discord