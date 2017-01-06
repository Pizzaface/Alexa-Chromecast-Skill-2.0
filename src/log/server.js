const http = require('http')

http.createServer((req, res) => {
  console.log(req.url, req.headers, req.method)
  req.on('data', (chunk) => console.log(chunk.toString()))
  return res.end(req.url)
}).listen(4000)

console.log('listening on port 4000')
