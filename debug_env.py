#!/usr/bin/env python3
import os
print("KIE_API_KEY from os.environ:", os.environ.get('KIE_API_KEY'))
print("USE_MOCK from os.environ:", os.environ.get('USE_MOCK'))
from app.config import Config
print("Config.KIE_API_KEY:", Config.KIE_API_KEY)
print("Config.USE_MOCK:", Config.USE_MOCK)
print("Config.KIE_API_BASE_URL:", Config.KIE_API_BASE_URL)