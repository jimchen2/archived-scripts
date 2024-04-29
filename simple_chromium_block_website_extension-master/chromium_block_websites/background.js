chrome.runtime.onInstalled.addListener(() => {
  fetch('block_websites.json')
    .then(response => response.json())
    .then(websites => {
      const rules = websites.map((website, index) => ({
        id: index + 1,
        priority: 1,
        action: {
          type: "block"
        },
        condition: {
          urlFilter: `||${website}`,
          resourceTypes: ["main_frame", "sub_frame"]
        }
      }));

      chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: rules.map(rule => rule.id),
        addRules: rules
      });
    })
    .catch(error => {
      console.error('Error fetching block_websites.json:', error);
    });
});
