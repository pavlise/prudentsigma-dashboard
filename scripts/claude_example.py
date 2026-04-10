import os
from anthropic import Anthropic, AsyncAnthropic

# Set your API key as an environment variable for security
API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not API_KEY:
    raise ValueError("Please set the ANTHROPIC_API_KEY environment variable.")

client = Anthropic(api_key=API_KEY)

# Example: Send a prompt to Claude
response = client.messages.create(
    model="claude-3-opus-20240229",  # Or another Claude model you have access to
    max_tokens=256,
    messages=[
        {"role": "user", "content": "Hello Claude!"}
    ]
)

print(response.content)
