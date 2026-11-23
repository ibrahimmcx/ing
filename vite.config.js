import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const ROOT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ALLOWED_ROOTS = new Map([
  ["/audio/", path.resolve(ROOT_DIR, "audio")],
  ["/data/", path.resolve(ROOT_DIR, "data")],
]);

const MIME_TYPES = {
  ".mp3": "audio/mpeg",
  ".json": "application/json; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
};

function workspaceMediaMiddleware(req, res, next) {
  if (!req.url || (req.method !== "GET" && req.method !== "HEAD")) {
    return next();
  }

  let pathname;
  try {
    pathname = decodeURIComponent(req.url.split("?")[0]);
  } catch {
    res.statusCode = 400;
    res.end("Bad request");
    return;
  }

  let targetRoot = null;
  let relPath = null;
  for (const [prefix, dirPath] of ALLOWED_ROOTS.entries()) {
    if (pathname.startsWith(prefix)) {
      targetRoot = dirPath;
      relPath = pathname.slice(prefix.length);
      break;
    }
  }

  if (!targetRoot || !relPath) {
    return next();
  }

  const resolved = path.resolve(targetRoot, relPath);
  if (!resolved.startsWith(targetRoot + path.sep)) {
    res.statusCode = 403;
    res.end("Forbidden");
    return;
  }

  let stat;
  try {
    stat = fs.statSync(resolved);
  } catch {
    res.statusCode = 404;
    res.end("Not found");
    return;
  }

  if (!stat.isFile()) {
    res.statusCode = 404;
    res.end("Not found");
    return;
  }

  const ext = path.extname(resolved).toLowerCase();
  const contentType = MIME_TYPES[ext] || "application/octet-stream";
  const fileSize = stat.size;
  const rangeHeader = req.headers.range;

  res.setHeader("Accept-Ranges", "bytes");
  res.setHeader("Content-Type", contentType);
  res.setHeader("Cache-Control", "no-cache");

  if (rangeHeader) {
    const match = /^bytes=(\d*)-(\d*)$/.exec(rangeHeader.trim());
    if (!match) {
      res.statusCode = 416;
      res.setHeader("Content-Range", `bytes */${fileSize}`);
      res.end();
      return;
    }

    let start = match[1] ? parseInt(match[1], 10) : 0;
    let end = match[2] ? parseInt(match[2], 10) : fileSize - 1;

    if (!match[1] && match[2]) {
      const suffix = parseInt(match[2], 10);
      start = Math.max(0, fileSize - suffix);
      end = fileSize - 1;
    }

    if (Number.isNaN(start) || Number.isNaN(end) || start > end || start >= fileSize) {
      res.statusCode = 416;
      res.setHeader("Content-Range", `bytes */${fileSize}`);
      res.end();
      return;
    }

    end = Math.min(end, fileSize - 1);
    const chunkSize = end - start + 1;

    res.statusCode = 206;
    res.setHeader("Content-Range", `bytes ${start}-${end}/${fileSize}`);
    res.setHeader("Content-Length", String(chunkSize));

    if (req.method === "HEAD") {
      res.end();
      return;
    }

    fs.createReadStream(resolved, { start, end }).pipe(res);
    return;
  }

  res.statusCode = 200;
  res.setHeader("Content-Length", String(fileSize));
  if (req.method === "HEAD") {
    res.end();
    return;
  }

  fs.createReadStream(resolved).pipe(res);
}

function serveWorkspaceMediaPlugin() {
  let isBuild = false;
  let outDir = path.resolve(ROOT_DIR, "dist");

  return {
    name: "serve-workspace-media",
    configResolved(config) {
      isBuild = config.command === "build";
      outDir = path.resolve(ROOT_DIR, config.build.outDir || "dist");
    },
    configureServer(server) {
      server.middlewares.use(workspaceMediaMiddleware);
    },
    configurePreviewServer(server) {
      server.middlewares.use(workspaceMediaMiddleware);
    },
    closeBundle() {
      if (!isBuild) return;

      const srcJson = path.resolve(ROOT_DIR, "data", "passages.json");
      const distDataDir = path.resolve(outDir, "data");
      if (fs.existsSync(srcJson)) {
        fs.mkdirSync(distDataDir, { recursive: true });
        fs.copyFileSync(srcJson, path.join(distDataDir, "passages.json"));
      }

      const srcAudio = path.resolve(ROOT_DIR, "audio");
      const distAudio = path.resolve(outDir, "audio");
      if (fs.existsSync(srcAudio)) {
        fs.cpSync(srcAudio, distAudio, { recursive: true });
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), serveWorkspaceMediaPlugin()],
  publicDir: false,
  server: {
    port: 5173,
    strictPort: false,
  },
});
