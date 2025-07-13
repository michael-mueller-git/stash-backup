FROM alpine:latest

RUN apk add --no-cache \
    openssh \
    sshfs \
    gocryptfs \
    rsync \
    fuse \
    python3 \
    py3-pip \
    py3-virtualenv

COPY requirements.txt .

# Create a virtualenv and install requirements inside it
RUN python3 -m virtualenv /venv && \
    . /venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Set PATH so all subsequent commands use the venv
ENV PATH="/venv/bin:$PATH"

RUN mkdir -p /root/.ssh /mnt/sshfs /mnt/decrypted /app

COPY entrypoint.sh /entrypoint.sh
COPY main.py /app/main.py
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

