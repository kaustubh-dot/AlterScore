const https = require("https");
const fs = require("fs");
const path = require("path");

const projectsDir = path.join(__dirname, "public", "projects");
const jsDir = path.join(__dirname, "public", "js");

// Ensure directories exist
if (!fs.existsSync(projectsDir)) {
  fs.mkdirSync(projectsDir, { recursive: true });
}
if (!fs.existsSync(jsDir)) {
  fs.mkdirSync(jsDir, { recursive: true });
}

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (response) => {
      if (response.statusCode === 301 || response.statusCode === 302) {
        downloadFile(response.headers.location, dest).then(resolve).catch(reject);
        return;
      }
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download ${url}: status code ${response.statusCode}`));
        return;
      }
      response.pipe(file);
      file.on("finish", () => {
        file.close(() => resolve(dest));
      });
    }).on("error", (err) => {
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

const projects = [
  "emerson",
  "mastercard",
  "nike",
  "kfc-loyalty",
  "de-rigo",
  "sara-assicurazioni",
  "tmov",
  "italo-cescon",
  "promotica",
  "subaru",
  "reebok",
  "areas",
  "rubensluciano",
  "bruno-presezzi",
  "grana-padano",
  "piacenti",
  "omron",
  "safe",
  "kfc-ai",
  "mavive",
  "flatman",
  "noleggio-lorini",
  "cuzziol-grandivini",
  "geopietra",
  "italmill",
  "mu-burger"
];

async function run() {
  try {
    console.log("Downloading lemon.js...");
    await downloadFile("https://lemon-engine.sidewave.it/lemon.js", path.join(jsDir, "lemon.js"));
    console.log("Downloaded lemon.js successfully.");

    console.log("Downloading usecases-list.json...");
    await downloadFile("https://sidewave.it/projects/usecases-list.json", path.join(projectsDir, "usecases-list.json"));
    console.log("Downloaded usecases-list.json successfully.");

    for (const project of projects) {
      const filename = `${project}.json`;
      console.log(`Downloading project JSON: ${filename}...`);
      await downloadFile(`https://sidewave.it/projects/${filename}`, path.join(projectsDir, filename));
      console.log(`Downloaded ${filename} successfully.`);
    }

    console.log("All project downloads completed successfully!");
  } catch (error) {
    console.error("Error during download:", error);
  }
}

run();
