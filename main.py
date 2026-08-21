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

intents=discord.Intents.default()