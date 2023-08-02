FROM node:16-slim as node-builder

WORKDIR /network-inspector/web

COPY ./web .

RUN cd ./server && npm ci && cd ../app && npm ci


FROM python:3.10-slim as pip-builder

WORKDIR /network-inspector

RUN pip install lxml=="4.9.2" beautifulsoup4=="4.12.2"


FROM node:16-slim AS scanner-builder

WORKDIR /network-inspector

RUN apt-get update && apt-get install -y \
    iproute2 \
    arp-scan \
    nmap \
    libxml2-utils \
    aircrack-ng \
    wireless-tools \
    isc-dhcp-client


FROM scanner-builder

WORKDIR /network-inspector

COPY --from=scanner-builder /network-inspector .
COPY --from=node-builder /network-inspector .
COPY --from=pip-builder /network-inspector .
COPY . .

RUN chmod +x ./setup.sh

EXPOSE 3000
EXPOSE 80

CMD ["./setup.sh"]
