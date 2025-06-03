document.addEventListener('DOMContentLoaded', function () {
  const grabButton = document.getElementById('grabButton');
  const statusDiv = document.getElementById('status');

  grabButton.addEventListener('click', async () => {
    statusDiv.textContent = 'Processing...';
    let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab) {
      statusDiv.textContent = 'Error: No active tab found.';
      return;
    }
    if (!tab.url || (!tab.url.startsWith('http:') && !tab.url.startsWith('https:'))) {
        statusDiv.textContent = 'Cannot access this page (e.g., chrome:// pages).';
        return;
    }


    try {
      // Ensure content script is injected
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });

      // Send message to content script
      const response = await chrome.tabs.sendMessage(tab.id, { action: "grabTable" });

      if (chrome.runtime.lastError) {
        statusDiv.textContent = 'Error: ' + chrome.runtime.lastError.message;
        console.error(chrome.runtime.lastError.message);
        return;
      }

      if (response && response.data) {
        navigator.clipboard.writeText(response.data)
          .then(() => {
            statusDiv.textContent = 'Table copied to clipboard!';
            setTimeout(() => window.close(), 1500); // Close popup after a delay
          })
          .catch(err => {
            statusDiv.textContent = 'Failed to copy.';
            console.error('Clipboard write failed: ', err);
          });
      } else if (response && response.error) {
        statusDiv.textContent = response.error;
      } else {
        statusDiv.textContent = 'No table data received.';
      }
    } catch (e) {
      statusDiv.textContent = 'Error: ' + e.message;
      console.error("Error during script execution or message sending:", e);
    }
  });
});