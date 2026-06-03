const fs = require("fs");
const zlib = require("zlib");
const path = require("path");

const files = [
  "public/Build/Sidewave_WebGL_260421_dxt.wasm.br",
  "public/Build/Sidewave_WebGL_260421_dxt.data.br",
  "public/Build/Sidewave_WebGL_260421_astc.wasm.br",
  "public/Build/Sidewave_WebGL_260421_astc.data.br"
];

function compressFile(filePath) {
  const data = fs.readFileSync(filePath);
  
  // Check if it's already compressed (if it starts with \0asm or UnityWebData it is raw)
  const isWasm = data.slice(0, 4).toString("hex") === "0061736d";
  const isData = data.slice(0, 12).toString() === "UnityWebData";
  
  if (isWasm || isData) {
    console.log(`Compressing ${filePath} with Brotli...`);
    const compressed = zlib.brotliCompressSync(data, {
      params: {
        [zlib.constants.BROTLI_PARAM_QUALITY]: 11,
      }
    });
    fs.writeFileSync(filePath, compressed);
    console.log(`Successfully compressed. Size: ${data.length} -> ${compressed.length} bytes.`);
  } else {
    console.log(`${filePath} is already Brotli compressed.`);
  }
}

function run() {
  for (const file of files) {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
      compressFile(filePath);
    } else {
      console.warn(`File not found: ${filePath}`);
    }
  }
  console.log("Compression tasks completed!");
}

run();
