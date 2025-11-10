// Store original order
let originalPlaylistOrder = [];
let currentlySorted = false;

// Function to extract comprehensive playlist data
function extractPlaylistData(playlistElement) {
  console.log('[PLAYLIST GROUPING] Extracting playlist data from element:', playlistElement);
  
  const data = {
    playlistId: null,
    firstVideoId: null,
    title: null,
    videoCount: null,
    updateStatus: null,
    visibility: null,
    playlistUrl: null,
    element: playlistElement // Store reference to DOM element
  };

  // Extract Playlist ID from multiple sources
  const contentIdClass = Array.from(playlistElement.classList).find(c => c.startsWith('content-id-'));
  if (contentIdClass) {
    data.playlistId = contentIdClass.replace('content-id-', '');
  }
  
  if (!data.playlistId) {
    const links = playlistElement.querySelectorAll('a[href*="list="]');
    for (const link of links) {
      if (link.href) {
        const urlParams = new URLSearchParams(new URL(link.href).search);
        const listId = urlParams.get('list');
        if (listId) {
          data.playlistId = listId;
          break;
        }
      }
    }
  }

  // Extract First Video ID
  const videoLink = playlistElement.querySelector('a[href*="watch?v="]');
  if (videoLink && videoLink.href) {
    const urlParams = new URLSearchParams(new URL(videoLink.href).search);
    data.firstVideoId = urlParams.get('v');
  }

  // Extract Playlist Title
  const titleElement = playlistElement.querySelector('.yt-lockup-metadata-view-model__title .yt-core-attributed-string');
  if (titleElement) {
    data.title = titleElement.textContent.trim();
  }

  // Extract Video Count
  const badgeElement = playlistElement.querySelector('.yt-badge-shape__text');
  if (badgeElement) {
    data.videoCount = badgeElement.textContent.trim();
  }

  // Extract Visibility and Update Status
  const metadataTexts = playlistElement.querySelectorAll('.yt-content-metadata-view-model__metadata-text');
  metadataTexts.forEach(el => {
    const text = el.textContent.trim();
    if (text.toLowerCase().includes('public') || text.toLowerCase().includes('private') || text.toLowerCase().includes('unlisted')) {
      data.visibility = text;
    } else if (text.toLowerCase().includes('updated')) {
      data.updateStatus = text;
    }
  });

  // Generate Playlist URL
  if (data.playlistId) {
    data.playlistUrl = `https://www.youtube.com/playlist?list=${data.playlistId}`;
  }

  console.log('[PLAYLIST GROUPING] Extracted data:', data);
  return data;
}

// Function to sort playlists alphabetically
function sortPlaylistsAlphabetically() {
  console.log('[PLAYLIST SORTING] Starting alphabetical sort...');
  
  const container = document.querySelector('#items.style-scope.ytd-grid-renderer');
  if (!container) {
    console.log('[PLAYLIST SORTING] Container not found');
    return false;
  }
  
  const playlists = Array.from(document.querySelectorAll('yt-lockup-view-model'));
  
  if (playlists.length === 0) {
    console.log('[PLAYLIST SORTING] No playlists found');
    return false;
  }
  
  // Store original order if not already stored
  if (originalPlaylistOrder.length === 0) {
    originalPlaylistOrder = playlists.map(el => el.cloneNode(true));
    console.log('[PLAYLIST SORTING] Stored original order:', originalPlaylistOrder.length, 'playlists');
  }
  
  // Extract playlist data with titles
  const playlistData = playlists.map(playlist => ({
    element: playlist,
    title: playlist.querySelector('.yt-lockup-metadata-view-model__title .yt-core-attributed-string')?.textContent?.trim() || ''
  }));
  
  // Sort by title
  playlistData.sort((a, b) => {
    return a.title.localeCompare(b.title, undefined, { sensitivity: 'base' });
  });
  
  console.log('[PLAYLIST SORTING] Sorted playlist order:', playlistData.map(p => p.title));
  
  // Clear container
  container.innerHTML = '';
  
  // Re-append in sorted order
  playlistData.forEach(item => {
    container.appendChild(item.element);
  });
  
  currentlySorted = true;
  console.log('[PLAYLIST SORTING] Playlists sorted alphabetically');
  
  // Re-process playlists to add tag UI
  setTimeout(() => {
    processPlaylistsOnPage();
  }, 100);
  
  return true;
}

// Function to restore original order
function restoreOriginalOrder() {
  console.log('[PLAYLIST SORTING] Restoring original order...');
  
  const container = document.querySelector('#items.style-scope.ytd-grid-renderer');
  if (!container || originalPlaylistOrder.length === 0) {
    console.log('[PLAYLIST SORTING] Cannot restore - no original order saved');
    return false;
  }
  
  // Clear container
  container.innerHTML = '';
  
  // Re-append in original order
  originalPlaylistOrder.forEach(playlistClone => {
    const freshClone = playlistClone.cloneNode(true);
    container.appendChild(freshClone);
  });
  
  currentlySorted = false;
  console.log('[PLAYLIST SORTING] Original order restored');
  
  // Re-process playlists to add tag UI
  setTimeout(() => {
    processPlaylistsOnPage();
  }, 100);
  
  return true;
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[PLAYLIST SORTING] Received message:', request);
  
  if (request.action === 'toggleAlphabetSort') {
    if (request.enabled) {
      const success = sortPlaylistsAlphabetically();
      sendResponse({ success });
    } else {
      const success = restoreOriginalOrder();
      sendResponse({ success });
    }
  }
  
  return true; // Will respond asynchronously
});

// Function to save playlist data to both local and sync storage
async function savePlaylistData(playlistId, playlistData, tags = []) {
  console.log('[PLAYLIST GROUPING] Saving playlist data for:', playlistId);
  
  // Don't save the DOM element reference
  const { element, ...dataToSave } = playlistData;
  
  const finalData = {
    ...dataToSave,
    tags: tags,
    lastUpdated: new Date().toISOString()
  };

  // Save to local storage
  const localData = await chrome.storage.local.get('playlistsData');
  const allLocalData = localData.playlistsData || {};
  allLocalData[playlistId] = finalData;
  await chrome.storage.local.set({ playlistsData: allLocalData });
  
  // Save to sync storage (with size limit handling)
  try {
    const syncData = await chrome.storage.sync.get('playlistsData');
    const allSyncData = syncData.playlistsData || {};
    allSyncData[playlistId] = finalData;
    await chrome.storage.sync.set({ playlistsData: allSyncData });
    console.log('[PLAYLIST GROUPING] Saved to both local and sync storage');
  } catch (error) {
    console.warn('[PLAYLIST GROUPING] Could not save to sync storage (quota exceeded?):', error);
    console.log('[PLAYLIST GROUPING] Data saved to local storage only');
  }
}

// Function to load playlist data from storage
async function loadPlaylistData(playlistId) {
  // Try local storage first
  const localData = await chrome.storage.local.get('playlistsData');
  const allLocalData = localData.playlistsData || {};
  
  if (allLocalData[playlistId]) {
    return allLocalData[playlistId];
  }
  
  // Fallback to sync storage
  const syncData = await chrome.storage.sync.get('playlistsData');
  const allSyncData = syncData.playlistsData || {};
  return allSyncData[playlistId] || null;
}

// Function to load and display tags for a specific playlist
async function loadAndDisplayTags(playlistId, tagsDisplayArea, playlistData) {
  console.log('[PLAYLIST GROUPING] Loading tags for playlist:', playlistId);
  
  // Clear existing tags to prevent duplicates
  tagsDisplayArea.innerHTML = '';
  
  const savedData = await loadPlaylistData(playlistId);
  const playlistTags = savedData?.tags || [];

  console.log('[PLAYLIST GROUPING] Found tags:', playlistTags);

  playlistTags.forEach(tagText => {
    const tagElement = document.createElement('span');
    tagElement.className = 'playlist-tag';
    tagElement.textContent = tagText;

    // Add a delete button (the 'x') to each tag
    const deleteBtn = document.createElement('span');
    deleteBtn.className = 'delete-tag-btn';
    deleteBtn.textContent = 'x';
    deleteBtn.title = 'Remove tag';
    deleteBtn.onclick = async (e) => {
        e.stopPropagation();
        e.preventDefault();
        
        console.log('[PLAYLIST GROUPING] Removing tag:', tagText);
        
        const currentData = await loadPlaylistData(playlistId);
        if (currentData) {
          const updatedTags = (currentData.tags || []).filter(t => t !== tagText);
          await savePlaylistData(playlistId, currentData, updatedTags);
          console.log('[PLAYLIST GROUPING] Tag removed, updated tags:', updatedTags);
          
          // Reload tags for this specific playlist only
          loadAndDisplayTags(playlistId, tagsDisplayArea, playlistData);
        }
    };

    tagElement.appendChild(deleteBtn);
    tagsDisplayArea.appendChild(tagElement);
  });
}

// Function to add the tag UI to a single playlist element
function addTagUI(playlistElement) {
  console.log('[PLAYLIST GROUPING] Processing playlist element:', playlistElement);
  
  // Check if we've already processed this element
  if (playlistElement.dataset.tagged === 'true') {
    console.log('[PLAYLIST GROUPING] Element already tagged, skipping');
    return;
  }
  playlistElement.dataset.tagged = 'true';

  // Extract all playlist data
  const playlistData = extractPlaylistData(playlistElement);
  
  if (!playlistData.playlistId) {
    console.log('[PLAYLIST GROUPING] Could not find playlist ID for element:', playlistElement);
    return;
  }
  
  console.log('[PLAYLIST GROUPING] Extracted playlist data:', playlistData);
  
  const metadataContainer = playlistElement.querySelector('yt-lockup-metadata-view-model .yt-lockup-metadata-view-model__text-container');
  if (!metadataContainer) {
    console.log('[PLAYLIST GROUPING] Could not find metadata container');
    return;
  }

  console.log('[PLAYLIST GROUPING] Found metadata container, adding tag UI');

  // Create UI elements
  const tagSectionContainer = document.createElement('div');
  tagSectionContainer.className = 'tag-section-container';

  const tagsDisplayArea = document.createElement('div');
  tagsDisplayArea.className = 'tags-display-area';
  
  const addTagButton = document.createElement('button');
  addTagButton.textContent = 'Add Tag';
  addTagButton.className = 'add-tag-btn';

  addTagButton.onclick = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('[PLAYLIST GROUPING] Add Tag button clicked for playlist:', playlistData.playlistId);
    
    const newTag = prompt('Enter a tag for this playlist:');
    if (newTag && newTag.trim() !== '') {
      console.log('[PLAYLIST GROUPING] Adding new tag:', newTag.trim());
      
      const currentData = await loadPlaylistData(playlistData.playlistId);
      const existingTags = currentData?.tags || [];
      
      if (!existingTags.includes(newTag.trim())) {
        existingTags.push(newTag.trim());
        console.log('[PLAYLIST GROUPING] Tag added successfully');
      } else {
        console.log('[PLAYLIST GROUPING] Tag already exists, skipping');
      }
      
      // Save complete data with updated tags
      await savePlaylistData(playlistData.playlistId, playlistData, existingTags);
      console.log('[PLAYLIST GROUPING] Saved to storage');
      
      // Reload tags for this specific playlist only
      loadAndDisplayTags(playlistData.playlistId, tagsDisplayArea, playlistData);
    }
  };
  
  tagSectionContainer.appendChild(tagsDisplayArea);
  tagSectionContainer.appendChild(addTagButton);
  metadataContainer.appendChild(tagSectionContainer);

  console.log('[PLAYLIST GROUPING] Tag UI added successfully');

  // Initial save of playlist data (without tags if none exist)
  loadPlaylistData(playlistData.playlistId).then(existingData => {
    if (!existingData) {
      savePlaylistData(playlistData.playlistId, playlistData, []);
    }
  });

  // Initial load of any saved tags
  loadAndDisplayTags(playlistData.playlistId, tagsDisplayArea, playlistData);
}

// Check if we're on a playlists page
function isOnPlaylistsPage() {
  const url = window.location.href;
  // Check if URL contains playlists path (e.g., youtube.com/@channel/playlists)
  return url.includes('/playlists') || url.includes('/@') && document.querySelector('ytd-grid-renderer');
}

// Process all playlists on the page
function processPlaylistsOnPage() {
    if (!isOnPlaylistsPage()) {
      console.log('[PLAYLIST GROUPING] Not on playlists page, skipping');
      return;
    }
    
    console.log('[PLAYLIST GROUPING] Processing playlists on page...');
    
    const playlistSelector = 'yt-lockup-view-model';
    const playlists = document.querySelectorAll(playlistSelector);
    
    console.log('[PLAYLIST GROUPING] Found', playlists.length, 'playlist elements');
    
    playlists.forEach((playlist, index) => {
      console.log('[PLAYLIST GROUPING] Processing playlist', index + 1, 'of', playlists.length);
      addTagUI(playlist);
    });
    
    // Check if we should apply alphabetical sort
    chrome.storage.local.get('alphabetSort', (data) => {
      if (data.alphabetSort && !currentlySorted) {
        console.log('[PLAYLIST SORTING] Auto-applying alphabetical sort from saved preference');
        setTimeout(() => {
          sortPlaylistsAlphabetically();
        }, 500);
      }
    });
}

// Listen for YouTube's navigation finish event
console.log('[PLAYLIST GROUPING] Setting up event listener for yt-navigate-finish...');
document.addEventListener("yt-navigate-finish", () => {
  console.log('[PLAYLIST GROUPING] yt-navigate-finish event fired');
  originalPlaylistOrder = []; // Reset on navigation
  currentlySorted = false;
  processPlaylistsOnPage();
});

// Run on initial load (with delay to ensure page is ready)
console.log('[PLAYLIST GROUPING] Extension loaded, waiting for initial processing...');
setTimeout(() => {
  console.log('[PLAYLIST GROUPING] Running initial playlist processing...');
  processPlaylistsOnPage();
}, 1500);

// Function to group playlists by tags
async function groupPlaylistsByTags() {
  console.log('[PLAYLIST GROUPING] Starting tag-based grouping...');
  
  const container = document.querySelector('#items.style-scope.ytd-grid-renderer');
  if (!container) {
    console.log('[PLAYLIST GROUPING] Container not found');
    return false;
  }
  
  const playlists = Array.from(document.querySelectorAll('yt-lockup-view-model'));
  
  if (playlists.length === 0) {
    console.log('[PLAYLIST GROUPING] No playlists found');
    return false;
  }
  
  // Store original order if not already stored
  if (originalPlaylistOrder.length === 0) {
    originalPlaylistOrder = playlists.map(el => el.cloneNode(true));
    console.log('[PLAYLIST GROUPING] Stored original order:', originalPlaylistOrder.length, 'playlists');
  }
  
  // Get all playlists with their tags
  const playlistsWithTags = await Promise.all(playlists.map(async (playlist) => {
    const data = extractPlaylistData(playlist);
    const savedData = await loadPlaylistData(data.playlistId);
    return {
      element: playlist,
      playlistId: data.playlistId,
      title: data.title,
      tags: savedData?.tags || []
    };
  }));
  
  // Group playlists by tags
  const tagGroups = {};
  const untagged = [];
  
  playlistsWithTags.forEach(item => {
    if (item.tags.length === 0) {
      untagged.push(item);
    } else {
      item.tags.forEach(tag => {
        if (!tagGroups[tag]) {
          tagGroups[tag] = [];
        }
        tagGroups[tag].push(item);
      });
    }
  });
  
  // Sort tag names alphabetically
  const sortedTagNames = Object.keys(tagGroups).sort((a, b) => 
    a.localeCompare(b, undefined, { sensitivity: 'base' })
  );
  
  console.log('[PLAYLIST GROUPING] Found tags:', sortedTagNames);
  console.log('[PLAYLIST GROUPING] Untagged playlists:', untagged.length);
  
  // Clear container
  container.innerHTML = '';
  
  // Add tagged groups
  sortedTagNames.forEach(tagName => {
    // Create tag header
    const header = document.createElement('div');
    header.className = 'tag-group-header';
    header.innerHTML = `
      <span>${tagName}</span>
      <span class="tag-count">${tagGroups[tagName].length}</span>
    `;
    container.appendChild(header);
    
    // Add playlists in this group
    // Remove duplicates by playlistId
    const seen = new Set();
    tagGroups[tagName].forEach(item => {
      if (!seen.has(item.playlistId)) {
        seen.add(item.playlistId);
        container.appendChild(item.element);
      }
    });
  });
  
  // Add untagged group if there are any
  if (untagged.length > 0) {
    const header = document.createElement('div');
    header.className = 'tag-group-header';
    header.style.borderLeftColor = '#666';
    header.innerHTML = `
      <span>Untagged</span>
      <span class="tag-count">${untagged.length}</span>
    `;
    container.appendChild(header);
    
    untagged.forEach(item => {
      container.appendChild(item.element);
    });
  }
  
  currentlySorted = true;
  console.log('[PLAYLIST GROUPING] Playlists grouped by tags');
  
  // Re-process playlists to add tag UI
  setTimeout(() => {
    processPlaylistsOnPage();
  }, 100);
  
  return true;
}

// Update the message listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[PLAYLIST SORTING] Received message:', request);
  
  if (request.action === 'toggleAlphabetSort') {
    if (request.enabled) {
      const success = sortPlaylistsAlphabetically();
      sendResponse({ success });
    } else {
      const success = restoreOriginalOrder();
      sendResponse({ success });
    }
  }
  
  if (request.action === 'toggleGroupByTags') {
    if (request.enabled) {
      groupPlaylistsByTags().then(success => {
        sendResponse({ success });
      });
    } else {
      const success = restoreOriginalOrder();
      sendResponse({ success });
    }
    return true; // Required for async response
  }
  
  return true;
});