# import os
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()

# client = OpenAI(
#     # This is the default and can be omitted
#     api_key=os.getenv("OPENAI_API_KEY")
# )

# completion = client.chat.completions.create(
#   model="gpt-3.5-turbo",
#   messages=[
#     {"role": "system", "content": "You are a helpful assistant."},
#     {"role": "user", "content": "Hello!"}
#   ]
# )

# print(completion.choices[0].message)


# client = OpenAI(
#   organization='org-OZlPXSviAlmOV9dx6fBtadBA',
#   project='proj_lcL6GVO4eMBuIwvqbBbbDTsk',
# )