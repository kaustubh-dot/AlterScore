import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const brotliAssetsPlugin = () => ({
  name: "brotli-assets-middleware",
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      if (req.url === "/log-error" && req.method === "POST") {
        let body = "";
        req.on("data", chunk => {
          body += chunk.toString();
        });
        req.on("end", () => {
          try {
            const data = JSON.parse(body);
            console.log("\x1b[31m[BROWSER LOG ERROR]\x1b[0m", data);
            const logPath = path.join(__dirname, "user_browser_errors.json");
            let logs = [];
            if (fs.existsSync(logPath)) {
              try {
                logs = JSON.parse(fs.readFileSync(logPath, "utf-8"));
              } catch (e) {
                logs = [];
              }
            }
            logs.push({ timestamp: new Date().toISOString(), ...data });
            fs.writeFileSync(logPath, JSON.stringify(logs, null, 2));
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ status: "ok" }));
          } catch (err) {
            res.writeHead(400);
            res.end("Invalid JSON");
          }
        });
        return;
      }

      const cleanUrl = req.url.split("?")[0];
      if (cleanUrl.endsWith(".br")) {
        const filePath = path.join(__dirname, "public", cleanUrl);
        if (fs.existsSync(filePath)) {
          const stats = fs.statSync(filePath);
          res.setHeader("Content-Encoding", "br");
          res.setHeader("Content-Length", stats.size);
          if (cleanUrl.endsWith(".wasm.br")) {
            res.setHeader("Content-Type", "application/wasm");
          } else if (cleanUrl.endsWith(".data.br")) {
            res.setHeader("Content-Type", "application/octet-stream");
          } else if (cleanUrl.endsWith(".js.br")) {
            res.setHeader("Content-Type", "application/javascript");
          }
          fs.createReadStream(filePath).pipe(res);
          return;
        }
      }
      next();
    });
  },
  configurePreviewServer(server) {
    server.middlewares.use((req, res, next) => {
      const cleanUrl = req.url.split("?")[0];
      if (cleanUrl.endsWith(".br")) {
        const filePath = path.join(__dirname, "public", cleanUrl);
        if (fs.existsSync(filePath)) {
          const stats = fs.statSync(filePath);
          res.setHeader("Content-Encoding", "br");
          res.setHeader("Content-Length", stats.size);
          if (cleanUrl.endsWith(".wasm.br")) {
            res.setHeader("Content-Type", "application/wasm");
          } else if (cleanUrl.endsWith(".data.br")) {
            res.setHeader("Content-Type", "application/octet-stream");
          } else if (cleanUrl.endsWith(".js.br")) {
            res.setHeader("Content-Type", "application/javascript");
          }
          fs.createReadStream(filePath).pipe(res);
          return;
        }
      }
      next();
    });
  }
});

export default defineConfig({
  plugins: [react(), brotliAssetsPlugin()],
  server: {
    host: "127.0.0.1",
    port: 5173,
  },
  preview: {
    host: "127.0.0.1",
    port: 4173,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (id.includes("three") || id.includes("@react-three")) {
              return "three-vendor";
            }
          }
        }
      }
    }
  }
});
