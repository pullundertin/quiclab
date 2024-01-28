FROM ubuntu:latest
WORKDIR /
COPY ./setup.sh /
RUN /setup.sh
COPY ./server/demo.py /aioquic/examples/
COPY ./client/http3_client.py /aioquic/examples/
COPY ./server/nginx.conf /etc/nginx/
COPY ./client/main.go /quic-go/example/client/
COPY ./server/main.go /quic-go/example/
COPY ./server/cubic_sender.go /quic-go/internal/congestion/
COPY ./server/sent_packet_handler.go /quic-go/internal/ackhandler



