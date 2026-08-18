import asyncio
import edge_tts

TEXT = "Robles likes to eat boneless pizza with ranch and can eat a weiner in one bite. He is a very good boy and loves to eat dogs."
VOICE = "en-US-AndrewNeural"
COMMUNICATION = edge_tts.Communicate(TEXT, VOICE)
OUTPUT_FILE = "edge_output.mp3"

async def generate_speech() -> None:
    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save(OUTPUT_FILE)

# Run the async function
asyncio.run(generate_speech())


# import asyncio
# import edge_tts

# async def list_voices() -> None:
#     voices = await edge_tts.VoicesManager.create()

#     # Filter for US English voices
#     us_voices = voices.find(Locale="en-US")

#     for voice in us_voices:
#         print(f"Name: {voice['Name']} | Gender: {voice['Gender']}")

# asyncio.run(list_voices())
