// Load saved preferences
chrome.storage.local.get(['alphabetSort', 'groupByTags'], (data) => {
  document.getElementById('alphabetSort').checked = data.alphabetSort || false;
  document.getElementById('groupByTags').checked = data.groupByTags || false;
});

// Handle alphabet sort toggle
document.getElementById('alphabetSort').addEventListener('change', async (e) => {
  const isChecked = e.target.checked;
  
  // If groupByTags is enabled, disable it
  if (isChecked && document.getElementById('groupByTags').checked) {
    document.getElementById('groupByTags').checked = false;
    await chrome.storage.local.set({ groupByTags: false });
  }
  
  // Save preference
  await chrome.storage.local.set({ alphabetSort: isChecked });
  
  // Send message to content script
  const tabs = await chrome.tabs.query({active: true, currentWindow: true});
  chrome.tabs.sendMessage(tabs[0].id, {
    action: 'toggleAlphabetSort',
    enabled: isChecked
  }, (response) => {
    if (response && response.success) {
      document.getElementById('status').textContent = isChecked ? 'Sorted A-Z' : 'Original order';
      setTimeout(() => {
        document.getElementById('status').textContent = '';
      }, 2000);
    }
  });
});

// Handle group by tags toggle
document.getElementById('groupByTags').addEventListener('change', async (e) => {
  const isChecked = e.target.checked;
  
  // If alphabetSort is enabled, disable it
  if (isChecked && document.getElementById('alphabetSort').checked) {
    document.getElementById('alphabetSort').checked = false;
    await chrome.storage.local.set({ alphabetSort: false });
  }
  
  // Save preference
  await chrome.storage.local.set({ groupByTags: isChecked });
  
  // Send message to content script
  const tabs = await chrome.tabs.query({active: true, currentWindow: true});
  chrome.tabs.sendMessage(tabs[0].id, {
    action: 'toggleGroupByTags',
    enabled: isChecked
  }, (response) => {
    if (response && response.success) {
      document.getElementById('status').textContent = isChecked ? 'Grouped by tags' : 'Original order';
      setTimeout(() => {
        document.getElementById('status').textContent = '';
      }, 2000);
    }
  });
});