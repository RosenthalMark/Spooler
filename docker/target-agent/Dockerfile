FROM node:20-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3 /usr/local/bin/python

WORKDIR /workspace

RUN mkdir -p /workspace/injected /opt/spooler/injection

CMD ["sh", "-c", "if [ -f /opt/spooler/injection/bootstrap.sh ]; then sh /opt/spooler/injection/bootstrap.sh; fi; tail -f /dev/null"]
