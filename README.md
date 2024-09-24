# py-cord-ollama
## Chat with LLM using discord threads feature
![](working.gif)

## Usage
Use a /chat command that will create a thread that you and your friends can respond to. 
Bot only responds to threads created by itself. <br>
Messages that will start with "-" in thread are invisible to llm. You can use it to discuss a response with someone without bot responding to it.

Not a lot of features because my friend needed it and i stitched it together on weekend and it's another dead project but it does what it was supposed to do so i am happy ¯\_(ツ)_/¯



## Commands

| Command    | Description                                                                                                                |
|------------|----------------------------------------------------------------------------------------------------------------------------|
| /versions  | Shows currently installed models on ollama instance                                                                        |
| /allmodels | Allows to prompt all models installed on ollama instance at the same time (creates a separate discord thread for each one) |
| /chat      | Creates a thread for selected model                                                                                        |


| Params     | Description                                                                                                                                                                                                         |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| model      | An exact name of model to be used for example llama3.1:latest or llama3.1:70b refer to https://ollama.com/library, it also has autocompletion to aid users with selecting the model                                 |
| prompt     | This is a first prompt that will kick of the model you can ask it what you would ask llm normally                                                                                                                   |
| threadname | This is a name of thread that will be created usefull when you are doing testing and potentially lots of different conversations will happen                                                                        |
| system     | This is an optional parameter if it's not set the default system prompt for llm will be used otherwise it will be forwarded to llm. By default it's something along "You are a helpful and knowledgeable Assistant" |

## Setup
I've setup this at home using docker refer to https://hub.docker.com/r/ollama/ollama <br>

### ollama
```bash
#Install ollama onto docker
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
#Download interesting model(s)
curl http://localhost:11434/api/pull -d '{
  "name": "llama3.1"
}'
```
### mybot
Edit with notepad main.py file replace token with your discord bot token and adjust url for api then
```bash
python3 main.py
```
MAKE SURE THAT YOU HAVE INTENT FOR READING CONTENT OF MESSAGES ENABLED ON DISCORD DEVELOPER PORTAL <br>
And it should be working

