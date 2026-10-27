# SentinelAI

Makine öğrenmesi destekli adaptif SSH honeypot (TÜBİTAK 2209-A çalışması).
Cowrie honeypot, kontrollü test istemcisi, özellik çıkarma ve sınıflandırma boru hattı.

## Klasörler
- cowrie/: docker-compose.yml (Cowrie kurulumu)
- client/: test istemcileri ve labels.csv
- features.py: loglardan oturum özellikleri
- train*.py: model ve ölçüm betikleri

## Not
Veri, izole laboratuvarda simülatörle üretilmiştir; gerçek saldırgan verisi değildir.
