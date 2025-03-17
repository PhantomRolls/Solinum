import ollama
import pandas as pd
from bs4 import BeautifulSoup

client = ollama.Client()
model1 = "llama3.1-FALC"
model2 = "llama3.2-note"

data = pd.read_csv("soliguide.csv", delimiter=';')
data=data[:600]
place_description = data['place_description']

place_description_unique = place_description.drop_duplicates()

with open("soliguide.html", "w", encoding="utf-8") as file1:
     with open("response.html", "w", encoding="utf-8") as file2:
    
        for i in range(1):
            soup = BeautifulSoup(str(place_description.iloc[50]), "html.parser")
            text = soup.get_text()
            print(text)
            file1.write(text + "\n")
            note = client.generate(model=model2, prompt=text)
            file1.write(note.response)
            file1.write("\n\n")
            
            response = client.generate(model=model1, prompt=text)
            file2.write(response.response)
            note = client.generate(model=model2, prompt=response.response)
            file2.write("\n")
            file2.write(note.response)
            file2.write("\n\n")




