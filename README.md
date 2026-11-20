OtakuNime — Web Nonton Anime (sub indo vibe, data legal)
=========================================================

Tampilan ala Otakudesu (grid ongoing + search + detail),
tapi data dari Jikan/MyAnimeList API (legal, gratis, tanpa API key).
Tombol nonton mengarah ke platform resmi (Crunchyroll, Netflix, Bilibili,
Muse Indonesia, iQIYI).

Jalankan di VPS (Ubuntu):
------------------------
1. Clone & venv:
   git clone https://github.com/ShouyaSawada/otakunime /root/OtakuNime
   cd /root/OtakuNime
   python3 -m venv ../OtakuNime_env
   source ../OtakuNime_env/bin/activate
   pip install -r requirements.txt

2. Tes cepat:
   python3 app.py          # http://IP-VPS:5000

3. Produksi (gunicorn):
   gunicorn -w 2 -b 0.0.0.0:5000 app:app

4. Biar jalan terus (systemd), buat /etc/systemd/system/otakunime.service:
   [Unit]
   Description=OtakuNime
   After=network.target
   [Service]
   WorkingDirectory=/root/OtakuNime
   ExecStart=/root/OtakuNime_env/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app
   Restart=always
   MemoryMax=150M
   [Install]
   WantedBy=multi-user.target

   lalu:
   systemctl daemon-reload
   systemctl enable --now otakunime

5. Buka port:
   ufw allow 5000

RAM dipakai < 100MB — aman untuk VPS 512MB.
Semua request ke Jikan di-cache 10 menit di memori (hemat kuota rate-limit 3 req/s).
