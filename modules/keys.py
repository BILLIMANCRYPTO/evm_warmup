# Получение приватных ключей из файла keys.txt
with open('keys.txt', 'r') as f:
    private_keys = [line.strip() for line in f]