# LecRec
**LecRec** is a `python` script that automatically records lectures from YouTube stream. **Unlike you, it has perfect attendance score**.

### Installation
To run the script, you need to install `yt-dlp`. The simplest way is to set up `venv` environment and install it there:
```bash
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install yt-dlp
```

### Configuration
Configuration is done through `schedule.json` config file. You can simply edit this file to add/remove lectures you need to record. **LecRec** automatically processes changes to configuration without the need to restart.

**LecRec** can record multiple lectures at once, which comes in handy if you were a bit too ambitious with your schedule.

### Run LecRec
Make sure you are in the `venv` environment and run the main script:
```bash
$ python3 lec_rec.py
```
To run the script in the background, use **systemd / cron / tmux**.
