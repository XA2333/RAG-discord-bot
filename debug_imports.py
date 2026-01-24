print("Basic Python works")
try:
    import discord
    print("Discord imported")
except ImportError:
    print("Discord failed")

try:
    import dotenv
    print("Dotenv imported")
except ImportError:
    print("Dotenv failed")
    
try:
    import pydantic
    print("Pydantic imported")
except ImportError:
    print("Pydantic failed")

try:
    import numpy
    print("Numpy imported")
except ImportError:
    print("Numpy failed")

try:
    import langchain
    print("Langchain imported")
except:
    print("Langchain crashed")

