# IP Scanner

多线程ping指定网段IP地址


### 部署

conda/mamba环境
```
mamba create -n ipsacnner python=3.10
```

venv环境部署
```
python -m venv .venv
```

安装
```
pip install -r requirements.txt
```


### 打包

```cmd
pyinstaller --onefile --name=IPScanner --icon=assets/favicon.ico app.py
```