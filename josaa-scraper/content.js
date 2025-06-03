chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "grabTable") {
    const tables = document.querySelectorAll('table');
    if (tables.length === 0) {
      sendResponse({ error: "No tables found on this page." });
      return true; // Keep message channel open for async response
    }

    // For simplicity, we grab the first table.
    // You could add logic here to select a specific table if multiple exist.
    const table = tables[0];
    let data = "";

    // Iterate over rows
    for (const row of table.rows) {
      let rowData = [];
      // Iterate over cells in the current row
      for (const cell of row.cells) {
        // .innerText tries to mimic rendered text, .textContent gets all text content
        // .trim() removes leading/trailing whitespace
        rowData.push(cell.innerText.trim().replace(/\s+/g, ' ')); // Replace multiple spaces with one
      }
      // Join cells with a comma, and rows with a newline
      data += rowData.join('#') + '\n';
    }

    if (data.trim() === "") {
        sendResponse({ error: "Selected table appears to be empty." });
    } else {
        sendResponse({ data: data });
    }
    return true; // Indicate that the response will be sent asynchronously (or synchronously in this case)
  }
});
