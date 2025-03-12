/*----- ----- ----- -----*/
// Member List Check
// For Albion Online "Tang Yuan" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/03/12
// Version: v2.1
/*----- ----- ----- -----*/

function memberListCheck() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Master");
  var lastRow = sheet.getLastRow();
  
  if (lastRow < 2) {
    Logger.log("Error: 'Master' tab doesn't have enough rows (need >= 2).");
    return;
  }
  
  // Get column indexes based on column titles
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var columnNames = ["Player", "In Guild", "Fight Role", "Past 7 Days", "Past 14 Days", "Past 28 Days", "Comment", "Mark"];
  var indexes = columnNames.map(name => headers.indexOf(name) + 1);

  // Check if any required column is missing
  var missingColumns = columnNames.filter((name, index) => indexes[index] === 0);
  if (missingColumns.length > 0) {
    Logger.log(`Error: The following required columns are missing: ${missingColumns.join(", ")}`);
    return;
  }

  // Extract individual column indexes
  var playerIndex = indexes[0]; 
  var inGuildIndex = indexes[1];
  var inFightRoleIndex = indexes[2];
  var past7Index = indexes[3];
  var past14Index = indexes[4];
  var past28Index = indexes[5];
  var commentIndex = indexes[6];
  var markIndex = indexes[7];
  
  // Read existing data
  var existingNames = sheet.getRange(2, playerIndex, lastRow - 1).getValues().flat();
  var inGuildStatus = sheet.getRange(2, inGuildIndex, lastRow - 1).getValues().flat();
  var markStatus = sheet.getRange(2, markIndex, lastRow - 1).getValues().flat();
  var past7Status = sheet.getRange(2, past7Index, lastRow - 1).getValues().flat();
  var past14Status = sheet.getRange(2, past14Index, lastRow - 1).getValues().flat();
  var past28Status = sheet.getRange(2, past28Index, lastRow - 1).getValues().flat();

  // Variables
  var guildId = "k0TF-1dGQLSBmWqusGHBHQ";
  var noDataString = "No data";

  // Fetch guild members from API
  var url = `https://gameinfo-sgp.albiononline.com/api/gameinfo/guilds/${guildId}/members`;
  var options = {
    "method": "GET",
    "headers": { "Accept": "application/json, text/plain, */*" },
    "muteHttpExceptions": true
  };

  try {
    var response = UrlFetchApp.fetch(url, options);
    if (response.getResponseCode() !== 200) {
      Logger.log(`Error: HTTP response code ${response.getResponseCode()}`);
      return;
    }

    var data = JSON.parse(response.getContentText());
    if (!data || data.length === 0) {
      Logger.log("Error: No data received from API.");
      return;
    }
    Logger.log("Successfully fetched member list!");
  } catch (error) {
    Logger.log(`Error during member list fetch: ${error}`);
    return;
  }

  var newNames = data.map(player => player.Name);

  // Identify new players
  var newEntries = newNames.filter(name => !existingNames.includes(name));

  // Identify last player in guild
  var lastYesRow = 1;
  for (var i = inGuildStatus.length - 1; i >= 0; i--) {
    if (inGuildStatus[i] === "Yes") {
      lastYesRow = i + 2;
      break;
    }
  }

  var today = new Date();
  var commentDate = Utilities.formatDate(today, "UTC", "dd/MM/yy");

  // Insert new players before deletion
  if (newEntries.length > 0) {
    newEntries.forEach(newName => {
      var newRowIndex = lastYesRow + 1;
      sheet.insertRowsAfter(lastYesRow, 1);
      var lastYesRowRange = sheet.getRange(lastYesRow, 1, 1, sheet.getLastColumn());
      var newRowRange = sheet.getRange(newRowIndex, 1, 1, sheet.getLastColumn());
      lastYesRowRange.copyTo(newRowRange, { formatOnly: true });
      sheet.getRange(newRowIndex, playerIndex).setValue(newName);
      sheet.getRange(newRowIndex, inGuildIndex).setValue("Yes");
      sheet.getRange(newRowIndex, commentIndex).setValue(commentDate + " new guild player added by bot");

      // Copy formula from previous row and apply to new row in "Fight Role"
      var prevFormula = sheet.getRange(lastYesRow, inFightRoleIndex).getFormula();
      if (prevFormula) {
        var updatedFormula = prevFormula.replace(/(\$?A)\d+/g, `$1${newRowIndex}`);
        sheet.getRange(newRowIndex, inFightRoleIndex).setFormula(updatedFormula);
      }

      lastYesRow++;
    });
  }

  // Delete old players
  for (var i = lastRow - 1; i >= 1; i--) {
    var currentStatus = inGuildStatus[i - 1];
    var past7Data = past7Status[i - 1];
    var past14Data = past14Status[i - 1];
    var past28Data = past28Status[i - 1];

    if (currentStatus === "No" && 
        String(past7Data).trim() === noDataString && 
        String(past14Data).trim() === noDataString && 
        String(past28Data).trim() === noDataString) {
      sheet.deleteRow(i + 1);
      lastRow--;
      Logger.log("One row deleted.");
      continue;
    }
  }

  // Save updated timestamp
  var searchText = "Player List Updated:";
  var formattedDate = Utilities.formatDate(new Date(), "UTC", "dd/MM/yyyy HH:mm");
  var range = sheet.getDataRange();
  var values = range.getValues();
  var rowIndex = -1, colIndex = -1;

  for (var row = 0; row < values.length; row++) {
    for (var col = 0; col < values[row].length; col++) {
      if (values[row][col] === searchText) {
        rowIndex = row + 1;
        colIndex = col + 2;
        break;
      }
    }
    if (rowIndex !== -1) break;
  }

  if (rowIndex !== -1 && colIndex !== -1) {
    sheet.getRange(rowIndex, colIndex).setValue(formattedDate);
    Logger.log("Member List Updated timestamp saved.");
  } else {
    Logger.log(`Error: "${searchText}" not found in sheet.`);
  }

  Logger.log("Member list updated!");
}
