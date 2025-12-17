/**
 * Google Apps Script - Random Question API
 * Deploy as Web App with "Execute as: Me" and "Who has access: Anyone"
 * This keeps the sheet private while allowing API access
 */

function doGet(e) {
  try {
    // Get the active spreadsheet
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // Get all data (skip header row)
    const data = sheet.getDataRange().getValues();
    const headers = data[0];
    const rows = data.slice(1);
    
    // Filter out empty rows
    const validRows = rows.filter(row => row[0] && row[1]); // Must have id and question
    
    if (validRows.length === 0) {
      return ContentService.createTextOutput(JSON.stringify({
        error: "No questions found in sheet"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // Select random question
    const randomIndex = Math.floor(Math.random() * validRows.length);
    const randomRow = validRows[randomIndex];
    
    // Build question object
    const question = {
      id: randomRow[0],
      question: randomRow[1],
      option_a: randomRow[2],
      option_b: randomRow[3],
      option_c: randomRow[4],
      option_d: randomRow[5],
      correct: randomRow[6],
      explanation: randomRow[7] || ""
    };
    
    // Return as JSON
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      data: question
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Test function - run this to verify the script works
 */
function testGetRandomQuestion() {
  const result = doGet();
  const content = result.getContent();
  Logger.log(content);
  return content;
}
