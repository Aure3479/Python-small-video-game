# Python small video game
 Small python game  using pygame to learn user study

Launch the game to defend yourself against zombies appearing to the sound of the beat you have chosen 
You have one life , if a zombie touches you it's game over.
But the closer you kill them the more points you get. 
You can use an arduino board with a button matrix to play, the directional arrows or the ZQSD buttons to defend yourself.

When you chose the music and put in a username the game will take some time to load the corresponding music when playing for the first time.

-----------------------------------------------------------------------------

For a user study we load all the different kinds of data at the end of a player's run. 
As long as the same user uses the same player name , the corresponding csv file of the player will be updated(or created) with those informations:
- Name: Name of player
- Score: Final score
- Total Blocks: number of zombies killed
- Just in Time: zombies killed that were close
- Normal: zombies killed that were at a normal distance
- Too Early: Zombies killed that were too far
- Up,Down,Left,Right: number of zombies killed in each direction 
- Start Time,End Time: Start and end time of the user
- Duration: time during the run 
- Music: name of the music 
- Average Reaction Time : Average reaction time from the moment a zombie showed up to it being dead

2 video demos are in the file : 
- one showing off how the game works and how it is registered in the corresponding csv file
- one (much shorter) showing off the pause button works


Python files: 
- test12.py is the main code 
- check_active_ports.py is used to check all the ports that are currently in use (use to decide wich COM your arduino is using)
- getpng_poeg.py is used to convert a svg file to png or jpeg file

Csv files : 
- Folder players : all the different players and their data around the game
- leaderboard.csv: leaderboard that is shown on the leaderboard page
- music_info.csv : info around the music files (generated from the jupyter notebook)

Musics: 
musics folder : all the .mp3 musics

Jupiter notebook: 
Analysis.ipnb : small analysis of user action around the game

Arduino code: 
controller_python_vg.ino: code that uses a matrix button to control the player character

Sprites folder: holds the player, zombie and explosion sprites

