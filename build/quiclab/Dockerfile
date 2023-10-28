FROM ubuntu:latest
WORKDIR /
COPY ./setup.sh /
RUN /setup.sh
COPY ./server/demo.py /aioquic/examples/
COPY ./server/nginx.conf /etc/nginx/
COPY ./client/main.go /quic-go/example/client/
COPY ./server/main.go /quic-go/example/



