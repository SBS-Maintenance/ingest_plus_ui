pyinstaller -w -F  --hidden-import=natsort.natsorted --add-data .\window.ui:.  .\ingest_plus_ui.py  --icon=.\icon.ico