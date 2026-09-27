# school-42.am

Статичный сайт Ереванской средней школы №42 им. Т. Шевченко (HTML/CSS/JS, без сборки).

Локальный просмотр: откройте `index.html` в браузере.

Деплой: каждый push в `main` выкладывает сайт на хостинг по FTPS (`.github/workflows/deploy.yml`).
Нужны secrets репозитория: `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`
(Settings → Secrets and variables → Actions). Папку на сервере задаёт `server-dir`.
