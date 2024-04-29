function blockRequest(details) {
  return {cancel: true};
}

async function updateBlockedWebsites() {
  try {
    const response = await fetch('block_websites.json');
    const websites = await response.json();
    const matchPatterns = websites.map(website => `*://*.${website}/*`);

    if (browser.webRequest.onBeforeRequest.hasListener(blockRequest)) {
      browser.webRequest.onBeforeRequest.removeListener(blockRequest);
    }

    browser.webRequest.onBeforeRequest.addListener(
      blockRequest,
      {urls: matchPatterns},
      ["blocking"]
    );
  } catch (error) {
    console.error('Error fetching block_websites.json:', error);
  }
}

browser.runtime.onInstalled.addListener(updateBlockedWebsites);
