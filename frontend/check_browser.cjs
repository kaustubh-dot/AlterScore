const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function run() {
  console.log("Launching headless browser...");
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  
  // Set viewport to standard desktop resolution
  await page.setViewport({ width: 1280, height: 720 });

  const consoleLogs = [];
  const pageErrors = [];
  const failedRequests = [];

  // Capture console logs
  page.on('console', msg => {
    consoleLogs.push(`[${msg.type().toUpperCase()}] ${msg.text()}`);
    console.log(`PAGE LOG: [${msg.type().toUpperCase()}] ${msg.text()}`);
  });

  // Capture uncaught exceptions
  page.on('pageerror', err => {
    pageErrors.push(err.toString());
    console.error(`PAGE EXCEPTION:`, err);
  });

  // Capture failed requests
  page.on('requestfailed', request => {
    failedRequests.push(`${request.url()} - ${request.failure().errorText}`);
    console.error(`REQUEST FAILED: ${request.url()} - ${request.failure().errorText}`);
  });

  // Capture HTTP errors (e.g. 404)
  page.on('response', response => {
    const status = response.status();
    if (status >= 400) {
      failedRequests.push(`HTTP ERROR ${status}: ${response.url()}`);
      console.error(`HTTP ERROR ${status}: ${response.url()}`);
    }
  });

  try {
    console.log("Navigating to http://127.0.0.1:5173/ ...");
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle2', timeout: 30000 });

    console.log("Waiting 14 seconds for loading animation to complete...");
    await new Promise(resolve => setTimeout(resolve, 14000));

    // Check preloader state
    const preloaderExists = await page.evaluate(() => {
      const el = document.querySelector('.preloader');
      return el ? {
        opacity: window.getComputedStyle(el).opacity,
        display: window.getComputedStyle(el).display,
        innerHtml: el.innerHTML.substring(0, 200)
      } : null;
    });
    console.log("Preloader State:", preloaderExists);

    // Capture screenshot before clicking
    await page.screenshot({ path: '/Users/ayush/.gemini/antigravity/brain/e4a45fb1-8e66-4aa5-87a8-067fffcbb114/scratch/preloader_loaded.png' });
    console.log("Captured preloader_loaded.png");

    // Click to start journey
    console.log("Clicking Begin Journey...");
    await page.click('.loader_icons');

    console.log("Waiting 5 seconds for exit animations and Unity initialization...");
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Capture screenshot after clicking
    await page.screenshot({ path: '/Users/ayush/.gemini/antigravity/brain/e4a45fb1-8e66-4aa5-87a8-067fffcbb114/scratch/after_click.png' });
    console.log("Captured after_click.png");

    // Check page metrics
    const metrics = await page.evaluate(() => {
      const loopLoader = document.querySelector('#loopLoader');
      const loopLoaderStyle = loopLoader ? {
        display: window.getComputedStyle(loopLoader).display,
        opacity: window.getComputedStyle(loopLoader).opacity,
        zIndex: window.getComputedStyle(loopLoader).zIndex
      } : null;

      const unityContainer = document.querySelector('#unityContainer');
      const webContainer = document.querySelector('#webContainer');

      return {
        bodyClass: document.body.className,
        documentElementClass: document.documentElement.className,
        bodyScrollHeight: document.body.scrollHeight,
        windowScrollY: window.scrollY,
        loopLoaderStyle,
        unityContainerExists: !!unityContainer,
        unityContainerHeight: unityContainer ? window.getComputedStyle(unityContainer).height : null,
        webContainerStyle: webContainer ? {
          display: window.getComputedStyle(webContainer).display,
          opacity: window.getComputedStyle(webContainer).opacity,
          position: window.getComputedStyle(webContainer).position
        } : null,
        timelineFrameCount: window.timelineFrameCount,
        enableAutoScroll: window.enableAutoScroll
      };
    });

    console.log("Page Metrics:", JSON.stringify(metrics, null, 2));

    // Evaluate snap scroll positions and simulate scroll to index 1
    const scrollResult = await page.evaluate(async () => {
      if (window.snapScroll) {
        const positions = window.snapScroll.getPositions();
        if (positions.length > 1) {
          // Programmatically scroll to the second snap position
          window.scrollTo(0, positions[1] + 20);
          window.dispatchEvent(new Event('scroll'));
          
          // Wait for any animations and visibility class updates
          await new Promise(resolve => setTimeout(resolve, 800));
          
          const siteShell = document.querySelector('.site-shell');
          const unityContainer = document.querySelector('#unityContainer');
          const webContainer = document.querySelector('#webContainer');
          const firstMenu = document.querySelector('.lateralMenu');
          const firstText = document.querySelector('.scroll-overlay-text');

          const detailedStyles = {
            siteShell: siteShell ? {
              className: siteShell.className,
              opacity: window.getComputedStyle(siteShell).opacity,
              zIndex: window.getComputedStyle(siteShell).zIndex,
              display: window.getComputedStyle(siteShell).display,
              position: window.getComputedStyle(siteShell).position
            } : null,
            unityContainer: unityContainer ? {
              className: unityContainer.className,
              opacity: window.getComputedStyle(unityContainer).opacity,
              zIndex: window.getComputedStyle(unityContainer).zIndex,
              display: window.getComputedStyle(unityContainer).display,
              position: window.getComputedStyle(unityContainer).position,
              height: window.getComputedStyle(unityContainer).height
            } : null,
            webContainer: webContainer ? {
              opacity: window.getComputedStyle(webContainer).opacity,
              zIndex: window.getComputedStyle(webContainer).zIndex,
              display: window.getComputedStyle(webContainer).display,
              position: window.getComputedStyle(webContainer).position
            } : null,
            firstMenu: firstMenu ? {
              className: firstMenu.className,
              opacity: window.getComputedStyle(firstMenu).opacity,
              zIndex: window.getComputedStyle(firstMenu).zIndex,
              display: window.getComputedStyle(firstMenu).display
            } : null,
            firstText: firstText ? {
              className: firstText.className,
              opacity: window.getComputedStyle(firstText).opacity,
              zIndex: window.getComputedStyle(firstText).zIndex,
              display: window.getComputedStyle(firstText).display
            } : null
          };
          
          const visibleMenus = Array.from(document.querySelectorAll('.lateralMenu.visible')).map(el => el.className);
          const visibleTexts = Array.from(document.querySelectorAll('.scroll-overlay-text.visible h2')).map(el => el.innerText);

          return {
            success: true,
            positions,
            currentScrollY: window.scrollY,
            detailedStyles,
            visibleMenus,
            visibleTexts
          };
        }
        return { success: false, reason: "No snap positions found or less than 2 positions" };
      }
      return { success: false, reason: "window.snapScroll is not defined" };
    });
    console.log("Scroll Simulation Result:", JSON.stringify(scrollResult, null, 2));

    // Capture screenshot after scrolling
    await page.screenshot({ path: '/Users/ayush/.gemini/antigravity/brain/e4a45fb1-8e66-4aa5-87a8-067fffcbb114/scratch/scrolled_view.png' });
    console.log("Captured scrolled_view.png");

  } catch (error) {
    console.error("Execution error:", error);
  } finally {
    await browser.close();
    console.log("Browser closed.");

    // Write final diagnostics to file
    const diagnostics = {
      consoleLogs,
      pageErrors,
      failedRequests
    };
    fs.writeFileSync(
      '/Users/ayush/.gemini/antigravity/brain/e4a45fb1-8e66-4aa5-87a8-067fffcbb114/scratch/diagnostics.json',
      JSON.stringify(diagnostics, null, 2)
    );
    console.log("Diagnostics written to diagnostics.json");
  }
}

run();
