#!/bin/bash

function help() {
      echo "Usage: netsim"
      echo -e "-c\t\tCLIENT\t\t\t\tcurl | aioquic"
      echo -e "-i\t\tFIREWALL\t\t\t0 | From:To"
      echo -e "-p\t\tPROTOCOL\t\t\thttp | https | quic | iperf"
      echo -e "-f\t\tFILE SIZE\t\t\tinteger in bytes"
      echo -e "-d\t\tDELAY\t\t\t\tinteger in ms"
      echo -e "-a\t\tDELAY DEVIATION\t\t\tinteger in ms"
      echo -e "-l\t\tLOSS\t\t\t\tinteger in %"
      echo -e "-r\t\tRATE\t\t\t\tinteger in Gbit"
      echo -e "-w\t\twindow scaling\t\t\t0/1"
      echo -e "--rmin\t\trecieve window minimum\t\tinteger in bytes"
      echo -e "--rdef\t\trecieve window default\t\tinteger in bytes"
      echo -e "--rmax\t\trecieve window maximum\t\tinteger in bytes"
      exit 1

}

function set_options() {

while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--client)
            CLIENT="$2"
            shift 2
            ;;
        -i|--firewall)
            FIREWALL="$2"
            shift 2
            ;;
        -p|--protocol)
            PROTO="$2"
            shift 2
            ;;
        -f|--file-size)
            FILE_SIZE="$2"
            shift 2
            ;;
        -d|--delay)
            DELAY="$2"
            shift 2
            ;;
        -a|--delay-deviation)
            DELAY_DEVIATION="$2"
            shift 2
            ;;
        -l|--loss)
            LOSS="$2"
            shift 2
            ;;
        -r|--rate)
            RATE="$2"
            shift 2
            ;;
        -w|--window-scaling)
            WINDOW_SCALING="$2"
            shift 2
            ;;
        --rmin)
            RMIN="$2"
            shift 2
            ;;
        --rdef)
            RDEF="$2"
            shift 2
            ;;
        --rmax)
            RMAX="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
			help
            exit 1
            ;;
    esac
done
}
