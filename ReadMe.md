Development run

```
python wireless_control.py
```    

Bundling

```
pyinstaller --onefile --windowed --add-data "logo.png:." wireless_control.py
```

Executing the Bundle
```
    cd dist
   ./wireless_control 
```