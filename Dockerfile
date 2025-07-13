FROM alpine:latest

RUN apk add --no-cache \
    openssh \
    sshfs \
    gocryptfs \
    rsync \
    fuse \
    python3 \
    py3-pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /root/.ssh /mnt/sshfs /mnt/decrypted /app

COPY entrypoint.sh /entrypoint.sh
COPY main.py /app/main.py
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

