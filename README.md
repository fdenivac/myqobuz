# myqobuz

Get or Set Qobuz playlists and favorites from command line

Use last version (>= 1.1) of [python-qobuz](https://github.com/fdenivac/python-qobuz) module supporting OAuth authentication.
<br>


# Installation
- Download / install [python-qobuz](https://github.com/fdenivac/python-qobuz), 
    ```
    pip install git+https://github.com/fdenivac/python-qobuz
    ```
- Download myqobuz script and install it anywhere
- Your application needs to be authenticated via OAuth :<br>
  on first use, or when authentication expires, execute :
    ```
    python myqobuz.py authenticate
    ```
    and follow instructions. The "**login**" section of config file ("_config.json_") will be now filled.


# Usage

Archive personal playlists and favorites :
``` 
myqobuz.py playlists > my_all_playlists.txt
myqobuz.py favorites > all_my_favorites.txt
```

Restore them :
``` 
myqobuz.py playlists-add --replace all_my_playlists.txt
myqobuz.py favorites-add  all_my_favorites.txt
```

Remove some tracks for a playlist :
- copy a previous output (*my_all_playlists*) to '*tracks_to_remove.txt*'
- modify this keeping only tracks to remove
The '*tracks_to_remove.txt*' file (only track id are mandatory):
```
        Playlist: "MyJazz", description: "", public: False, collaborative: False
          13757514 | Jan Garbarek                             | Atmos                                              | Atmos 
          40071709
        Playlist: "MyRock", description: "", public: False, collaborative: False
          23265470
```
And remove tracks:
``` 
myqobuz.py playlists-del tracks_to_remove.txt
```

Create a new playlist :
- Prepare a new file '*myselection.txt*':
```
    Playlist: "A new selection", description: "My preferred song", public: False, collaborative: False
      66370200 | Nils Landgren | 4 Wheel Drive Live | Lobito 
      631787   | Nick Drake  | Five Leaves Left  | River Man 
```
- and create :
``` 
myqobuz.py playlists-add  myselection.txt
```
