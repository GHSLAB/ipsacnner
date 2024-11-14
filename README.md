# IP Scanner
[中文](README_CN.md)

Multi-threaded Pinging IP address

<div style="display: flex; justify-content: space-around;">
    <img src="assets/image01.png" alt="image1" style="width: 25%;"/>
    <img src="assets/image02.png" alt="image2" style="width: 25%;"/>
</div>

### Deployment

Conda/Mamba environment
```cmd
mamba create -n ipsacnner python=3.10
```

Venv environment
```cmd
python -m venv .venv
call .venv/Scripts/activate
```

Installation
```cmd
pip install -r requirements.txt
```

### Packaging

```cmd
pyinstaller --onefile --name=IPScanner --icon=assets/favicon.ico app.py
```
