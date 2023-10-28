package main

import (
	"bufio"
	"context"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"

	_ "net/http/pprof"

	"github.com/quic-go/quic-go"
	"github.com/quic-go/quic-go/http3"
	"github.com/quic-go/quic-go/internal/testdata"
	"github.com/quic-go/quic-go/internal/utils"
	"github.com/quic-go/quic-go/logging"
	"github.com/quic-go/quic-go/qlog"
)

type binds []string

func (b binds) String() string {
	return strings.Join(b, ",")
}

func (b *binds) Set(v string) error {
	*b = strings.Split(v, ",")
	return nil
}

// Size is needed by the /demo/upload handler to determine the size of the uploaded file
type Size interface {
	Size() int64
}

// See https://en.wikipedia.org/wiki/Lehmer_random_number_generator
func generatePRData(l int) []byte {
	res := make([]byte, l)
	seed := uint64(1)
	for i := 0; i < l; i++ {
		seed = seed * 48271 % 2147483647
		res[i] = byte(seed)
	}
	return res
}

func setupHandler(www string) http.Handler {
	mux := http.NewServeMux()


	// Handler for /data.log path
	mux.HandleFunc("/data.log", func(w http.ResponseWriter, r *http.Request) {
		// Open the data.log file
		filePath := "/data/data.log"
		file, err := os.Open(filePath)
		if err != nil {
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}
		defer file.Close()

		// Copy the file content to the response writer
		_, err = io.Copy(w, file)
		if err != nil {
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}
	})

	return mux
}

func main() {
	// defer profile.Start().Stop()
	go func() {
		log.Println(http.ListenAndServe("localhost:6060", nil))
	}()
	// runtime.SetBlockProfileRate(1)

	verbose := flag.Bool("v", false, "verbose")
	bs := binds{}
	flag.Var(&bs, "bind", "bind to")
	www := flag.String("www", "", "www data")
	tcp := flag.Bool("tcp", false, "also listen on TCP")
	enableQlog := flag.Bool("qlog", false, "output a qlog (in the same directory)")
	flag.Parse()

	logger := utils.DefaultLogger

	if *verbose {
		logger.SetLogLevel(utils.LogLevelDebug)
	} else {
		logger.SetLogLevel(utils.LogLevelInfo)
	}
	logger.SetLogTimeFormat("")

	if len(bs) == 0 {
		bs = binds{"0.0.0.0:6121"}
	}

	handler := setupHandler(*www)
	quicConf := &quic.Config{}
	if *enableQlog {
		quicConf.Tracer = func(ctx context.Context, p logging.Perspective, connID quic.ConnectionID) *logging.ConnectionTracer {
			filename := fmt.Sprintf("/shared/qlog_server/server_%x.qlog", connID)
			f, err := os.Create(filename)
			if err != nil {
				log.Fatal(err)
			}
			log.Printf("Creating qlog file %s.\n", filename)
			return qlog.NewConnectionTracer(utils.NewBufferedWriteCloser(bufio.NewWriter(f), f), p, connID)
		}
	}

	var wg sync.WaitGroup
	wg.Add(len(bs))
	for _, b := range bs {
		bCap := b
		go func() {
			var err error
			if *tcp {
				certFile, keyFile := testdata.GetCertificatePaths()
				err = http3.ListenAndServe(bCap, certFile, keyFile, handler)
			} else {
				server := http3.Server{
					Handler:    handler,
					Addr:       bCap,
					QuicConfig: quicConf,
				}
				err = server.ListenAndServeTLS(testdata.GetCertificatePaths())
			}
			if err != nil {
				fmt.Println(err)
			}
			wg.Done()
		}()
	}
	wg.Wait()
}
