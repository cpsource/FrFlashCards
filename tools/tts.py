from gtts import gTTS

text = """À l'issue de la conférence de San Francisco organisée en juin 1945 alors que la guerre faisait encore rage dans le Pacifique, cinquante-et-un États signaient la Charte établissant une organisation internationale qui prendra le nom de Nations unies. Elle entre en vigueur le 24 octobre 1945, il y a tout juste huit décennies."""

tts = gTTS(text=text, lang='fr', slow=False)
tts.save("les-nations-unies.mp3")
