# MiguelitoBot (TheCollerinesBot)

## Requirements

Runs with python 3 =)

Install dependencies (Linux):
```
pip3 install python-telegram-bot —upgrade
```
```
pip3 install unidecode
```
```
pip3 install spotipy
```
```
pip3 install python-dateutil --user
```
## Start

Use "python3" or your configurated command for version 3

```
python3 ./collerinesBot.py
```

### Windows
Install dependencies:
```
pip install python-telegram-bot
```
```
pip install unidecode
```
```
pip install spotipy
```
```
pip install python-dateutil --user
```
## Start

Use "python3" or your configurated command for version 3

```
python ./collerinesBot.py
```

## For test

We need to change the token value in config.ini file: token=<token_id value> with a token given by botFather (ask for more info ;) ;) )

After that, we need to change the groupid value in config.ini too because MiguelitoBot is filtered for just one group (for private use :) ) 

### How to get the groupId
```
Add the bot in a group with read permission and just send a message.
After that you need to go to:

https://api.telegram.org/bot< bot token_id value >/getUpdates

And save the chat_id value in config.ini with groupid name.
```

## Youtube and Spotify Api
Register the app in next links and save the api keys, client_id and client_secret values in config.ini:

https://developer.spotify.com/my-applications

https://console.developers.google.com/apis/credentials

If you want to censor a word or a song, just add it in youtubeCensor.json array object.

## Required files for correct functionaly
youtubeCensor.json -> ```["string", "string"]```

dateConfig.json -> 
```
{
  "name": "mañana",
  "value": "1",
  "type": "day"
}, {
  "name": "pasado",
  "value": "2",
  "type": "day"
}]
```

userNames.json -> 
```
[{
	"name": "keyword",
	"value": "telegramId"
}]
```

## How work Miguelito
### Commands
#### Add Youtube songs to Spotify List
```
Miguelito añade Numb Linkin Park -- 
Miguelito añade <songname> <groupName - Not necessary if is the first song in Spotify with the songname> 

```
``` 
<some text>  https://www.youtube.com/watch?v=hJ_eVIZkjZE --
<some text>  <youtube link video wt complete url or shorted url>
Miguelito get the video name and remove all text that be inside () and [] to search in Spotify API.
If he can't find the song he will try with the different video-tags of youtube

```

## Extraball
### Send messages like a ninja

https://api.telegram.org/bot< bot token_id value >/sendMessage?chat_id=< chat_id value >&text=< text_value >

## Special Thanks

Spotipy is from -> https://github.com/plamere/spotipy 
