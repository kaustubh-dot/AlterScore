const https = require("https");
const fs = require("fs");
const path = require("path");

const files = [
  // Fonts
  { url: "https://sidewave.it/fonts/PPFormula-CondensedBlack.woff2", dest: "public/fonts/PPFormula-CondensedBlack.woff2" },
  { url: "https://sidewave.it/fonts/fraktionsans-regular-webfont.woff2", dest: "public/fonts/fraktionsans-regular-webfont.woff2" },
  { url: "https://sidewave.it/fonts/FraktionMono-Regular.woff2", dest: "public/fonts/FraktionMono-Regular.woff2" },
  { url: "https://sidewave.it/fonts/PPFormula-CondensedBlack.woff", dest: "public/fonts/PPFormula-CondensedBlack.woff" },
  { url: "https://sidewave.it/fonts/fraktionsans-regular-webfont.woff", dest: "public/fonts/fraktionsans-regular-webfont.woff" },
  { url: "https://sidewave.it/fonts/FraktionMono-Regular.woff", dest: "public/fonts/FraktionMono-Regular.woff" },

  // Images
  { url: "https://sidewave.it/images/Mobius100.gif", dest: "public/images/Mobius100.gif" },
  { url: "https://sidewave.it/images/Mobius9.gif", dest: "public/images/Mobius9.gif" },
  { url: "https://sidewave.it/images/SW_Logo_W.svg", dest: "public/images/SW_Logo_W.svg" },
  { url: "https://sidewave.it/images/menu_origin.webp", dest: "public/images/menu_origin.webp" },
  { url: "https://sidewave.it/images/menu_about.webp", dest: "public/images/menu_about.webp" },
  { url: "https://sidewave.it/images/menu_services.webp", dest: "public/images/menu_services.webp" },
  { url: "https://sidewave.it/images/menu_usecases.webp", dest: "public/images/menu_usecases.webp" },
  { url: "https://sidewave.it/images/menu_contacts.webp", dest: "public/images/menu_contacts.webp" },

  // JS files
  { url: "https://sidewave.it/js/unity-loader.js", dest: "public/js/unity-loader.js" },
  { url: "https://sidewave.it/js/ui-interactions.js", dest: "public/js/ui-interactions.js" },
  { url: "https://sidewave.it/js/scroll-navigation.js", dest: "public/js/scroll-navigation.js" },
  { url: "https://sidewave.it/js/scroll-visuals.js", dest: "public/js/scroll-visuals.js" },
  { url: "https://sidewave.it/js/translator.js", dest: "public/js/translator.js" },
  { url: "https://sidewave.it/js/cookieconsent.umd.js", dest: "public/js/cookieconsent.umd.js" },
  { url: "https://sidewave.it/js/ai-chat.js", dest: "public/js/ai-chat.js" },
  { url: "https://sidewave.it/js/cookie.js", dest: "public/js/cookie.js" },

  // Unity build files - Desktop
  { url: "https://sidewave.it/Build/Sidewave_WebGL_260421_dxt.loader.js", dest: "public/Build/Sidewave_WebGL_260421_dxt.loader.js" },
  { url: "https://sidewave.it/Build/Sidewave_WebGL_260421_dxt.framework.js", dest: "public/Build/Sidewave_WebGL_260421_dxt.framework.js" },
  { url: "https://sidewave.it/Build/Sidewave_WebGL_260421_dxt.wasm.br", dest: "public/Build/Sidewave_WebGL_260421_dxt.wasm.br" },
  { url: "https://sidewave.it/Build/Sidewave_WebGL_260421_dxt.data.br", dest: "public/Build/Sidewave_WebGL_260421_dxt.data.br" },

  // Unity build files - Mobile
  { url: "https://sidewave.it/Build/Sidewave_WebGL_260421_astc.loader.js", dest: "public/Build/Sidewave_WebGL_260421_astc.loader.js" },
  { url: "https://sidewave.it/Build/Sidewave_WebGL_260421_astc.framework.js", dest: "public/Build/Sidewave_WebGL_260421_astc.framework.js" },
  { url: "https://sidewave.it/Build/Sidewave_WebGL_260421_astc.wasm.br", dest: "public/Build/Sidewave_WebGL_260421_astc.wasm.br" },
  { url: "https://sidewave.it/Build/Sidewave_WebGL_260421_astc.data.br", dest: "public/Build/Sidewave_WebGL_260421_astc.data.br" }
];

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    
    https.get(url, (response) => {
      if (response.statusCode === 301 || response.statusCode === 302) {
        // Follow redirect
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

async function run() {
  console.log(`Starting download of ${files.length} assets...`);
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const absDest = path.join(__dirname, file.dest);
    console.log(`[${i + 1}/${files.length}] Downloading ${file.url} -> ${file.dest}...`);
    try {
      await downloadFile(file.url, absDest);
      console.log(`   Success: ${file.dest}`);
    } catch (e) {
      console.error(`   Error downloading ${file.url}: ${e.message}`);
    }
  }
  console.log("All asset downloads completed!");
}

run();
