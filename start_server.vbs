Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\Axioo Hype 1\OneDrive\Dokumen\spada_umg"
WshShell.Run "python manage.py runserver 0.0.0.0:8000 --noreload", 0, False
