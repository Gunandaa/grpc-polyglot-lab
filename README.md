# gRPC Polyglot Lab

Tutorial praktikum komunikasi inter-service dengan gRPC. Satu server **Go** dipanggil oleh dua client berbeda bahasa: **Python** dan **Node.js**, dengan satu kontrak `user.proto` sebagai sumber kebenaran tunggal.

Panduan ini ditulis untuk **Windows + Git Bash**.

## Struktur Proyek

```
grpc-polyglot-lab/
├── .gitignore
├── README.md
├── user.proto
├── go-server/
│   ├── go.mod
│   ├── go.sum
│   ├── main.go
│   └── pb/
│       ├── user.pb.go
│       └── user_grpc.pb.go
├── python-client/
│   ├── client.py
│   ├── user_pb2.py
│   └── user_pb2_grpc.py
└── node-client/
    ├── client.js
    ├── package.json
    └── package-lock.json
```

## Prasyarat

Pasang perangkat berikut, lalu **tutup dan buka ulang Git Bash** agar PATH terbaca.

| Perangkat | Sumber | Catatan |
|-----------|--------|---------|
| Git | git-scm.com | Pastikan Git Bash ikut terpasang |
| Python 3.10+ | python.org | Centang **Add Python.exe to PATH** |
| Node.js (LTS) | nodejs.org | Sudah termasuk npm |
| Go | go.dev/dl | |
| protoc | github.com/protocolbuffers/protobuf/releases | Unduh `protoc-xx.x-win64.zip` |

### Memasang protoc di Windows

1. Ekstrak `protoc-xx.x-win64.zip` ke `C:\protoc` sehingga ada `C:\protoc\bin\protoc.exe`.
2. Daftarkan ke PATH Git Bash:

   ```bash
   echo 'export PATH="$PATH:/c/protoc/bin:$HOME/go/bin"' >> ~/.bashrc
   echo '[ -f ~/.bashrc ] && source ~/.bashrc' >> ~/.bash_profile
   source ~/.bashrc
   ```

3. Verifikasi seluruh instalasi:

   ```bash
   git --version
   python --version
   node -v
   npm -v
   go version
   protoc --version
   ```

> Jika `python` tidak dikenali, coba `py --version`, lalu pakai `py` sebagai pengganti `python` di seluruh langkah.
> Saat mengetik perintah, selalu gunakan dua tanda hubung biasa (`--proto_path`), bukan tanda hubung panjang.

## Langkah 1: Setup Workspace dan Git

```bash
mkdir grpc-polyglot-lab
cd grpc-polyglot-lab
git init
```

Jika Git belum diatur identitasnya:

```bash
git config --global user.name "Nama Kamu"
git config --global user.email "email@kamu.com"
```

Buat `.gitignore` dan commit pertama:

```bash
echo "node_modules/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".venv/" >> .gitignore
echo "*.exe" >> .gitignore
git add .gitignore
git commit -m "Initial commit: Add gitignore rules"
```

## Langkah 2: Menulis Kontrak API

Buat `user.proto` **di folder utama** `grpc-polyglot-lab`:

```proto
syntax = "proto3";

package user;

option go_package = "./pb";

message UserRequest {
  int32 user_id = 1;
}

message UserResponse {
  string name = 1;
  string email = 2;
}

service UserService {
  rpc GetUserProfile (UserRequest) returns (UserResponse);
}
```

## Langkah 3: gRPC Server (Go)

Semua perintah dijalankan dari folder utama `grpc-polyglot-lab`.

```bash
mkdir go-server
cd go-server
go mod init go-server
go get google.golang.org/grpc
go get google.golang.org/protobuf
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
```

Generate kode Go dari kontrak:

```bash
protoc --proto_path=../ --go_out=. --go-grpc_out=. ../user.proto
ls pb
```

Folder `pb` harus berisi `user.pb.go` dan `user_grpc.pb.go`.

Buat `go-server/main.go`:

```go
package main

import (
	"context"
	"fmt"
	"log"
	"net"

	"go-server/pb"

	"google.golang.org/grpc"
)

type server struct {
	pb.UnimplementedUserServiceServer
}

func (s *server) GetUserProfile(ctx context.Context, req *pb.UserRequest) (*pb.UserResponse, error) {
	log.Printf("Menerima request untuk User ID: %d\n", req.GetUserId())
	if req.GetUserId() == 1 {
		return &pb.UserResponse{
			Name:  "Budi Santoso",
			Email: "budi@universitas.ac.id",
		}, nil
	}
	return &pb.UserResponse{
		Name:  "User Tidak Ditemukan",
		Email: "-",
	}, nil
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Gagal listening port: %v", err)
	}
	s := grpc.NewServer()
	pb.RegisterUserServiceServer(s, &server{})
	fmt.Println("gRPC Server (Go) berjalan di port :50051...")
	if err := s.Serve(lis); err != nil {
		log.Fatalf("Gagal menjalankan server: %v", err)
	}
}
```

Rapikan dependensi:

```bash
go mod tidy
```

## Langkah 4: Client Python

```bash
cd ..
mkdir python-client
cd python-client
pip install grpcio grpcio-tools
python -m grpc_tools.protoc --proto_path=../ --python_out=. --grpc_python_out=. ../user.proto
ls
```

Harus muncul `user_pb2.py` dan `user_pb2_grpc.py`.

Buat `python-client/client.py`:

```python
import grpc
import user_pb2
import user_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        print("Mengirim request ke Go Server menggunakan Python...")
        response = stub.GetUserProfile(user_pb2.UserRequest(user_id=1))
        print(f"Respon dari Server -> Nama: {response.name}, Email: {response.email}")

if __name__ == '__main__':
    run()
```

## Langkah 5: Client Node.js

```bash
cd ..
mkdir node-client
cd node-client
npm init -y
npm install @grpc/grpc-js @grpc/proto-loader
```

Node.js tidak memerlukan proses generate: `user.proto` dibaca langsung saat program berjalan.

Buat `node-client/client.js`:

```js
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');

const PROTO_PATH = path.join(__dirname, '../user.proto');
const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
});
const userProto = grpc.loadPackageDefinition(packageDefinition).user;

function main() {
    const client = new userProto.UserService('localhost:50051', grpc.credentials.createInsecure());
    console.log("Mengirim request ke Go Server menggunakan Node.js...");
    client.GetUserProfile({ user_id: 1 }, (error, response) => {
        if (!error) {
            console.log(`Respon dari Server -> Nama: ${response.name}, Email: ${response.email}`);
        } else {
            console.error("Terjadi error:", error);
        }
    });
}
main();
```

## Langkah 6: Pengujian

Buka **3 jendela Git Bash** terpisah.

**Terminal 1: server Go (biarkan tetap berjalan)**

```bash
cd go-server
go run main.go
```

**Terminal 2: client Python**

```bash
cd python-client
python client.py
```

**Terminal 3: client Node.js**

```bash
cd node-client
node client.js
```

Hasil yang benar:

- Python dan Node.js sama-sama mencetak data `Budi Santoso` beserta emailnya.
- Terminal server mencetak `Menerima request untuk User ID: 1` setiap ada client yang memanggil.
- Tidak ada error `Connection refused` atau `Cannot find module`.

## Langkah 7: Push ke GitHub

Buat repository **kosong** di GitHub (tanpa README dan tanpa .gitignore), lalu dari folder utama:

```bash
git add .
git commit -m "Feat: Add full polyglot implementation of Go server, Python client, and Node client"
git branch -M main
git remote add origin https://github.com/USERNAME/NAMA_REPO.git
git push -u origin main
```

Jika muncul `remote origin already exists`, ganti alamatnya dengan:

```bash
git remote set-url origin https://github.com/USERNAME/NAMA_REPO.git
```

## Langkah 8: Menambah Field `phone`

**1. Ubah `user.proto`:**

```proto
message UserResponse {
  string name = 1;
  string email = 2;
  string phone = 3;
}
```

**2. Generate ulang Go dan ubah `main.go`:**

```bash
cd go-server
protoc --proto_path=../ --go_out=. --go-grpc_out=. ../user.proto
```

Tambahkan `Phone` pada kedua respons di `main.go`:

```go
if req.GetUserId() == 1 {
    return &pb.UserResponse{
        Name:  "Budi Santoso",
        Email: "budi@universitas.ac.id",
        Phone: "081234567890",
    }, nil
}
return &pb.UserResponse{
    Name:  "User Tidak Ditemukan",
    Email: "-",
    Phone: "-",
}, nil
```

**3. Generate ulang Python dan ubah `client.py`:**

```bash
cd ../python-client
python -m grpc_tools.protoc --proto_path=../ --python_out=. --grpc_python_out=. ../user.proto
```

Ubah baris print:

```python
print(f"Respon dari Server -> Nama: {response.name}, Email: {response.email}, Telepon: {response.phone}")
```

**4. Ubah `client.js`** (tanpa generate ulang):

```js
console.log(`Respon dari Server -> Nama: ${response.name}, Email: ${response.email}, Telepon: ${response.phone}`);
```

**5. Restart server** (`Ctrl+C`, lalu `go run main.go`) dan jalankan ulang kedua client. Nomor telepon harus ikut tercetak.

## Analisis Pendekatan Kompilasi

Pada pendekatan *static code generation* (Go dan Python), file `user.proto` dikompilasi terlebih dahulu menggunakan `protoc` (atau `grpc_tools.protoc` di Python) sebelum program dijalankan. Hasilnya berupa file kode sumber nyata (`user.pb.go` dan `user_grpc.pb.go` untuk Go, `user_pb2.py` dan `user_pb2_grpc.py` untuk Python) yang diimpor langsung ke dalam program. Keuntungannya, tipe data diperiksa saat kompilasi atau pengembangan, dukungan autocomplete lebih baik, dan performa lebih optimal karena kode serialisasi sudah tersedia. Kekurangannya, setiap kali skema `.proto` berubah, developer wajib menjalankan ulang proses generate agar kode tetap sinkron dengan kontrak terbaru.

Sebaliknya, pada pendekatan *dynamic runtime generation* (Node.js), tidak ada langkah kompilasi terpisah. Library `@grpc/proto-loader` membaca file `user.proto` langsung saat aplikasi berjalan (`loadSync`), lalu membangun definisi service dan message di dalam memori. Akibatnya, perubahan skema seperti penambahan field `phone` langsung terbaca setelah client dijalankan ulang, tanpa proses generate dan tanpa file hasil kompilasi di repositori. Pendekatan ini lebih fleksibel dan cepat untuk prototipe, tetapi tidak ada pemeriksaan tipe saat kompilasi, dan aplikasi bergantung pada keberadaan file `.proto` saat runtime sehingga kesalahan baru ketahuan ketika program dijalankan.

## Masalah Umum

| Pesan error | Penyebab | Solusi |
|-------------|----------|--------|
| `protoc: command not found` | `protoc` belum masuk PATH | Ikuti bagian **Memasang protoc di Windows**, lalu buka ulang Git Bash |
| `protoc-gen-go: program not found` | `%USERPROFILE%\go\bin` belum masuk PATH | Jalankan `export PATH="$PATH:$(go env GOPATH)/bin"` |
| `Could not make proto path relative: ../user.proto` | Folder client salah tempat, atau perintah dijalankan dari folder yang salah | Pastikan folder berada di dalam `grpc-polyglot-lab`, lalu jalankan dari dalam subfolder (cek dengan `pwd`) |
| `The current directory is invalid` | Terminal masih terikat ke lokasi lama folder yang dipindah | Tutup lalu buka ulang Git Bash |
| `Connection refused` / `UNAVAILABLE` | Server Go belum berjalan | Jalankan `go run main.go` di Terminal 1 terlebih dahulu |
| `Cannot find module` | `npm install` belum dijalankan atau salah folder | Masuk ke `node-client`, lalu `npm install` |
| `ModuleNotFoundError: user_pb2` | Proto belum dikompilasi untuk Python | Jalankan perintah `grpc_tools.protoc` di dalam `python-client` |
| `remote origin already exists` | Remote sudah pernah dipasang | Gunakan `git remote set-url origin <URL>` |