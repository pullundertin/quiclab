FROM ubuntu
WORKDIR /
COPY ./setup.sh /
COPY ./data.log /data/
RUN /setup.sh
COPY ./demo.py /aioquic/examples/
COPY ./nginx.conf /etc/nginx/

