FROM ubuntu
WORKDIR /
COPY ./setup.sh /
RUN /setup.sh
COPY ./demo.py /aioquic/examples/
COPY ./nginx.conf /etc/nginx/

