## Sample location file
This script will read sample location from yaml file. The format example is below: 
```yaml
- { name: Paris, longitude: 2.2945, latitude: 48.8584, height: 35.0 }
- { name: Toulouse, longitude: 1.4808, latitude: 43.5606, height: 146.0 }
- { name: StMichel, longitude: -1.5115, latitude: 48.6360, height: 52.0 }
```


## Useful command
Run locally
```bash
uv sync
uv run main.py -h
```

```bash
uv run main.py nice -t 10 -s 3
```

Create single executable binary：
```bash
pyinstaller -F --name gga main.py
```

Simulate GPS devices
```bash
socat  PTY,link=/tmp/ttyV0,raw,echo=0 EXEC:"gga paris -t 10 -s 0.5"
```