import os

os.environ["DATABASE_URL"] = "sqlite:///./test_sellpy.db"
os.environ["SELLPY_REMINDERS"] = "false"
os.environ["ANTHROPIC_API_KEY"] = "teste"
os.environ["WHATSAPP_VERIFY_TOKEN"] = "token-de-teste"
os.environ["WHATSAPP_APP_SECRET"] = "segredo-de-teste"
