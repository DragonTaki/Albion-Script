/*----- ----- ----- -----*/
// Member List Check
// For Albion Online "Tang Yuan" Guild only
// Do not distribute or modified
// Author: DragonTaki(https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/03/08
// Version: v1.2
/*----- ----- ----- -----*/

function memberListCheck() {
  // URL Query
  // "Tang Yuan" Guild ID "k0TF-1dGQLSBmWqusGHBHQ"
  var url = "https://gameinfo-sgp.albiononline.com/api/gameinfo/guilds/k0TF-1dGQLSBmWqusGHBHQ/members";
  
  // Use get option
  var options = {
    "method": "GET",
    "headers": {
      "Accept": "application/json, text/plain, */*"
    },
    "muteHttpExceptions": true
  };
  
  try {
    // Fetch player list
    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    
    if (responseCode !== 200) {
      Logger.log(`Error: HTTP response code ${responseCode}`);
      return;
    }
    
    // If needed print this
    var rawResponse = response.getContentText();
    //Logger.log(`Raw Response: ${rawResponse}`);

    var data = JSON.parse(rawResponse);
    
    // Check if data valid
    if (!data || data.length === 0) {
      Logger.log("Error: No data received from API.");
      return;
    } else {
        Logger.log("Successfully fetched member list!");
    }
  } catch (error) {
    Logger.log(`Error during member list fetch: ${error}`);
  }

  var newNames = data.map(player => player.Name); // Get member list from API
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Master");
  var lastRow = sheet.getLastRow();
  
  // If no data in 'Master' tab
  if (lastRow < 2) {
    Logger.log("Error: 'Master' tab don't have enough lines (need >= 2).");
    return;
  }
  
  // Get player names (Column A)
  var existingNames = sheet.getRange('A2:A' + sheet.getLastRow()).getValues().flat();
  var newEntries = newNames.filter(name => !existingNames.includes(name)); // Find out who is new

  // Get if in guild (Column B)
  var statusList = sheet.getRange('B2:B' + sheet.getLastRow()).getValues().flat();

  // Find out the last player in guild, will insert new player after it
  var lastYesRow = 1;
  for (var i = statusList.length - 1; i >= 0; i--) {
    if (statusList[i] === "Yes") {
      lastYesRow = i + 2; // i0 equal A2
      break;
    }
  }

  var today = new Date();
  var commentDate = Utilities.formatDate(today, "UTC", "dd/MM/yy");

  existingNames.forEach((name, index) => {
    var currentStatus = newNames.includes(name) ? "Yes" : "No"; // Check if player still in guild
    var previousStatus = statusList[index][0]; // Check player's prev status

    // If player's guild status no changed, do nothing
    // If player's guild status changed, update his/hers status
    if (currentStatus !== previousStatus) {
      sheet.getRange(index + 2, 2).setValue(currentStatus);
      var comment = "";
      if (previousStatus === "No" && currentStatus === "Yes") {
        comment = commentDate + " back to guild checked by bot";
      } else if (previousStatus === "Yes" && currentStatus === "No") {
        comment = commentDate + " left guild checked by bot";
      }
      if (comment) {
        sheet.getRange(index + 2, 9).setValue(comment); // I 欄記錄
      }
    }
  });
  
  if (newEntries.length > 0) {

    // Insert new player after last player in guild
    newEntries.forEach(newName => {
      var newRowIndex = lastYesRow + 1;
      sheet.insertRowsAfter(lastYesRow, 1);

      var lastYesRowRange = sheet.getRange(lastYesRow, 1, 1, sheet.getLastColumn());
      var newRowRange = sheet.getRange(newRowIndex, 1, 1, sheet.getLastColumn());
      lastYesRowRange.copyTo(newRowRange, {formatOnly: true});

      sheet.getRange(newRowIndex, 1).setValue(newName);
      sheet.getRange(newRowIndex, 2).setValue("Yes");
      sheet.getRange(newRowIndex, 9).setValue(commentDate + " new guild player added by bot"); 

      lastYesRow++;
    });
  }

  // Save updated timestamp
  var searchText = "Player List Updated:";
  var currentDate = new Date();
  var formattedDate = Utilities.formatDate(currentDate, "UTC", "dd/MM/yyyy HH:mm");
  var range = sheet.getDataRange();
  var values = range.getValues();
  var rowIndex = -1;
  var colIndex = -1;

  for (var row = 0; row < values.length; row++) {
    for (var col = 0; col < values[row].length; col++) {
      if (values[row][col] === searchText) {
        rowIndex = row + 1; // Google Sheet index start from 1
        colIndex = col + 2; // Write down right cell
        break;
      }
    }
    if (rowIndex !== -1) break;
  }

  if (rowIndex !== -1 && colIndex !== -1) {
    sheet.getRange(rowIndex, colIndex).setValue(formattedDate);
    Logger.log("Member List Updated timestamp saved at row " + rowIndex + ", col " + colIndex);
  } else {
    Logger.log(`Error: "${searchText}" not found in sheet.`);
  }
  
  Logger.log("Member list updated!");
}
