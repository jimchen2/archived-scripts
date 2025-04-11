const puppeteer = require("puppeteer");
const fs = require("fs");

// --- Puppeteer Script ---

// Load cookies from file
function loadCookies() {
  try {
    const cookiesString = fs.readFileSync("./cookies.json", "utf8");
    return JSON.parse(cookiesString);
  } catch (error) {
    console.error("Error loading cookies:", error.message);
    return null;
  }
}

// Launch the browser
async function launchBrowser() {
  return await puppeteer.launch({
    headless: false, // Set to true for headless mode
    defaultViewport: null,
    args: ["--window-size=1366,768"],
  });
}

// Collect conversation URLs from the chats page
async function collectConversationUrls(page) {
  console.log("Collecting conversation URLs...");
  try {
    await page.waitForSelector("li.styles_Conversation__IoGWS", { timeout: 15000 }); // Wait up to 15s
  } catch (e) {
    console.warn("Conversation list items (li.styles_Conversation__IoGWS) did not appear in time. No URLs collected.");
    return [];
  }

  const conversationUrls = await page.evaluate(() => {
    const baseUrl = window.location.origin;
    const conversationItems = document.querySelectorAll("li.styles_Conversation__IoGWS");
    const urls = [];
    conversationItems.forEach((item) => {
      const linkElement = item.querySelector("a.styles_conversationLink__w7AZy");
      if (linkElement) {
        const relativeUrl = linkElement.getAttribute("href");
        if (relativeUrl) {
          const fullUrl = relativeUrl.startsWith("http") ? relativeUrl : baseUrl + relativeUrl;
          urls.push(fullUrl);
        }
      }
    });
    return urls;
  });

  console.log(`Found ${conversationUrls.length} conversation URLs.`);
  return conversationUrls;
}

// Extract messages from a conversation page
async function extractMessages(page) {
  // Wait for message elements to exist before trying to extract
  try {
    await page.waitForSelector("div.styles_message__5GLGe", { timeout: 10000 }); // Wait up to 10s
  } catch (e) {
    console.warn("No message elements (div.styles_message__5GLGe) found on the page within timeout.");
    return []; // Return empty if no messages found
  }

  return await page.evaluate(() => {
    // Selectors for message types - these are critical and might change
    const messageSelector = "div.styles_message__5GLGe";
    const userMessageClass = "styles_out__Cf_m_";
    const partnerMessageClass = "styles_in__UXyUs";
    const textMessageSelector = ".styles_textMessage__8y01H p";
    const imageMessageSelector = ".styles_imageMessage__FSbXV img";
    const commentMessageSelector = ".styles_commentMessage__rZRHc";
    const commentOriginalSelector = ".styles_original__Zwz94 p";
    const commentTextSelector = ".styles_comment__1eS_M p";

    const messageElements = document.querySelectorAll(messageSelector);
    const messages = [];

    messageElements.forEach((msgElement) => {
      let sender = "Unknown";
      let messageData = null;

      // Determine sender
      if (msgElement.classList.contains(userMessageClass)) {
        sender = "User";
      } else if (msgElement.classList.contains(partnerMessageClass)) {
        sender = "Partner";
      }

      // Check for text message
      const textParagraph = msgElement.querySelector(textMessageSelector);
      if (textParagraph) {
        messageData = {
          sender: sender,
          type: "text",
          content: textParagraph.textContent.trim(),
        };
      } else {
        // Check for image message
        const imageElement = msgElement.querySelector(imageMessageSelector);
        if (imageElement) {
          messageData = {
            sender: sender,
            type: "image",
            content: imageElement.getAttribute("src"), // Get image URL
          };
        } else {
          // Check for comment message (reply)
          const commentMessageDiv = msgElement.querySelector(commentMessageSelector);
          if (commentMessageDiv) {
            const originalTextElement = commentMessageDiv.querySelector(commentOriginalSelector);
            const commentTextElement = commentMessageDiv.querySelector(commentTextSelector);
            if (originalTextElement && commentTextElement) {
              messageData = {
                sender: sender,
                type: "comment",
                content: commentTextElement.textContent.trim(),
                commentedOn: originalTextElement.textContent.trim(),
              };
            } else {
              // Fallback if specific comment structure isn't found but it's a comment div
              messageData = { sender: sender, type: "comment", content: commentMessageDiv.innerText.trim(), commentedOn: "Unknown Original" };
              console.warn("Could not extract specific original/comment text, grabbing whole comment div text.");
            }
          } else {
            // Add checks for other message types if needed (e.g., voice, system messages)
            // If none of the above, log it as unknown
            console.log("Unknown message type found:", msgElement.innerHTML.substring(0, 100)); // Log beginning of unknown message HTML
            messageData = { sender: sender, type: "unknown", content: msgElement.innerText.trim() };
          }
        }
      }

      if (messageData) {
        messages.push(messageData);
      }
    });

    return messages;
  });
}

// --- Function to get profile URL from Chat page ---
async function getPartnerProfileUrl(page) {
  console.log("Attempting to find partner's profile link on chat page...");
  // Wait for the potential link element to appear
  const profileLinkSelector = ".styles_name__MFxv7 a"; // Selector for the link around the partner's name
  try {
    await page.waitForSelector(profileLinkSelector, { timeout: 5000 });
  } catch (e) {
    console.warn(`Partner profile link selector ('${profileLinkSelector}') not found on chat page.`);
    return null;
  }

  const profileUrl = await page.evaluate((selector) => {
    const linkElement = document.querySelector(selector);
    // Ensure href is absolute
    return linkElement ? linkElement.href : null;
  }, profileLinkSelector); // Pass selector to evaluate

  if (profileUrl) {
    console.log(`Found profile URL: ${profileUrl}`);
  } else {
    console.warn(`Profile link element found, but 'href' attribute was missing or empty.`);
  }
  return profileUrl;
}

// Save conversations and profiles to file
function saveConversations(data) {
  const filename = "./tandem_data.json";
  console.log(`Saving extracted data to ${filename}...`);
  try {
    fs.writeFileSync(filename, JSON.stringify(data, null, 2));
    console.log("Data saved successfully.");
  } catch (error) {
    console.error(`Error saving data to ${filename}:`, error.message);
  }
}

// Main function
async function main() {
  const cookies = loadCookies();
  if (!cookies) {
    console.error("Failed to load cookies. Exiting.");
    return;
  }

  const browser = await launchBrowser();
  const page = await browser.newPage(); // Create page once

  try {
    // Set cookies
    await page.setCookie(...cookies);
    console.log("Cookies set.");

    // Navigate to chats page
    const chatsPageUrl = "https://app.tandem.net/ru/chats"; // Make sure this is correct
    console.log(`Navigating to chats page: ${chatsPageUrl}...`);
    await page.goto(chatsPageUrl, { waitUntil: "networkidle2", timeout: 60000 }); // Increased timeout for initial load
    console.log("Chats page loaded.");

    // Collect conversation URLs
    const conversationUrls = await collectConversationUrls(page);

    if (conversationUrls.length === 0) {
      console.warn("No conversation URLs found. Check the page structure or CSS selectors. Exiting.");
      await browser.close();
      return;
    }

    // Array to store all extracted conversation and profile data
    const allExtractedData = [];
    let totalMessagesExtracted = 0;
    let profilesScraped = 0;
    let profileScrapeErrors = 0;

    // Visit each conversation URL, extract messages, find profile, scrape profile
    for (let i = 0; i < conversationUrls.length; i++) {
      const chatUrl = conversationUrls[i];
      console.log(`\n--- Processing Conversation ${i + 1}/${conversationUrls.length} ---`);
      console.log(`Navigating to chat: ${chatUrl}...`);

      let extractedMessages = [];
      let partnerProfileUrl = null;
      let profileData = null;

      try {
        await page.goto(chatUrl, { waitUntil: "networkidle2", timeout: 45000 }); // Timeout for chat load
        console.log(`Chat page ${chatUrl} loaded.`);

        // 1. Extract messages
        extractedMessages = await extractMessages(page);
        console.log(`Extracted ${extractedMessages.length} messages.`);
        totalMessagesExtracted += extractedMessages.length;

        // 2. Get partner's profile URL from the chat page
        partnerProfileUrl = await getPartnerProfileUrl(page);

        // // 3. If profile URL found, navigate and scrape
        // if (partnerProfileUrl) {
        //   console.log(`Navigating to profile: ${partnerProfileUrl}...`);

        //   try {
        //     await page.goto(partnerProfileUrl);
        //     console.log(`Navigated to ${partnerProfileUrl}, checking content...`);

        //     let hasContainer = false;
        //     let profileData = null;

        //     try {
        //       // First, check if any content exists
        //       const bodyText = await page.evaluate(() => document.body.innerText);
        //       console.log("Page body text length:", bodyText.length);

        //       // Then check for our specific selector and grab the data directly
        //       profileData = await page.evaluate(() => {
        //         const container = document.querySelector(".styles_container__8pJcv");
        //         if (container) {
        //           // Return the container's outer HTML as requested
        //           return container.outerHTML;
        //         }
        //         return null;
        //       });

        //       hasContainer = !!profileData;
        //       console.log("Container exists on page:", hasContainer);
        //     } catch (error) {
        //       console.error("Error during page evaluation:", error);
        //     }

        //     if (profileData) {
        //       profilesScraped++;
        //     } else {
        //       console.warn(`Profile container not found for ${partnerProfileUrl}. Check the selector.`);
        //       profileScrapeErrors++;
        //     }
        //   } catch (profileError) {
        //     console.error(`Error navigating to or scraping profile ${partnerProfileUrl}:`, profileError.message);
        //     profileScrapeErrors++;
        //   }
        // } else {
        //   console.warn(`Could not find profile URL for chat ${chatUrl}. Skipping profile scrape.`);
        //   profileScrapeErrors++; // Count as an error/miss
        // }

        // 4. Store collected data for this conversation
        allExtractedData.push({
          chatUrl: chatUrl,
          partnerProfileUrl: partnerProfileUrl || "Not Found", // Store the URL we tried (or null)
          messages: extractedMessages,
          profileData: profileData, // Will be null if scraping failed or wasn't attempted
        });
      } catch (error) {
        console.error(`Error processing chat ${chatUrl}:`, error.message);
        // Store partial data if messages were extracted before error
        allExtractedData.push({
          chatUrl: chatUrl,
          partnerProfileUrl: partnerProfileUrl || "Error occurred before check",
          messages: extractedMessages, // Store any messages collected before error
          profileData: null, // Profile data is null due to error
          error: `Processing failed: ${error.message}`, // Add error info
        });
      }
    } // End of loop through conversation URLs

    // Save extracted conversations and profiles to a file
    saveConversations(allExtractedData);

    // Log summary
    console.log("\n--- Extraction Summary ---");
    console.log(`Processed ${conversationUrls.length} conversations.`);
    console.log(`Total messages extracted: ${totalMessagesExtracted}`);
    console.log(`Profiles successfully scraped: ${profilesScraped}`);
    console.log(`Profile scrape attempts failed or skipped: ${profileScrapeErrors}`);
    console.log(`Detailed data saved to tandem_data.json`);
  } catch (error) {
    console.error("An unexpected error occurred in the main process:", error);
  } finally {
    // Close browser
    console.log("Closing browser...");
    await browser.close();
    console.log("Browser closed.");
  }
}

// Run the script
main();
