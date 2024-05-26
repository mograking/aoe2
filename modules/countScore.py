
import json
import sqlite3
import re
import requests
import apis_
import pandas as pd
import discord

import os
from dotenv import load_dotenv
load_dotenv()


sqlc =sqlite3.connect('discordToAoe.db') 
cr = sqlc.cursor()
