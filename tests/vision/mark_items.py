from openai import OpenAI
import base64

client = OpenAI(api_key="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")

result = client.images.edit(
    model="gpt-image-1",
    image=[open(r"tests\vision\images\woman_futuristic.jpg", "rb"), open(r"tests\vision\images\brain_logo.png", "rb")],
    prompt="Add the logo to the woman's top, as if stamped into the fabric.",
    input_fidelity="high"
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)

# Save the image to a file
with open("woman_with_logo.png", "wb") as f:
    f.write(image_bytes)