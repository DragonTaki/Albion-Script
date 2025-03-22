/*----- ----- ----- -----*/
// MemberListCheck.gs
// For Albion Online "Tang Yuan" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/03/20
// Version: v3.1
/*----- ----- ----- -----*/

function memberListCheck() {
  // Variables for user
  var sheetName = "Master";
  //var sheetName = "Copy of Master";
  var noDataString = "No data";
  var inGuildYes = "Yes";
  var inGuildNo = "No";

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) {
    msgLogger(`Sheet "${sheet}" not found.`, "e");
    return;
  }
  var lastCol = sheet.getLastColumn();
  var lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    msgLogger(`Sheet "${sheet}" doesn't have enough rows (need >= 2).`, "e");
    return;
  }
  
  // Get column indexes based on column titles
  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var columnNames = ["Player", "In Guild", "Fight Role", "Past 7 Days", "Past 14 Days", "Past 28 Days", "Comment", "Force Mark"];
  var indexes = columnNames.map(name => headers.indexOf(name) + 1);

  // Check if any required column is missing
  if (indexes.includes(0)) {
    msgLogger(`Missing required columns: ${columnNames.filter((_, i) => indexes[i] === 0).join(", ")}.`, "e");
    return;
  }

  // Extract individual column indexes
  var [playerIndex, inGuildIndex, inFightRoleIndex, past7Index, past14Index, past28Index, commentIndex, markIndex] = indexes;
  
  // Read existing data efficiently
  var dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol);
  var data = dataRange.getValues();

  var existingNames = new Map();
  var inGuildStatus = new Map();
  
  if (!data || data.length === 0) {
    msgLogger(`No data retrieved from the sheet ${sheetName}.`, "e");
    return;
  }

  data.forEach((row, i) => {
    if (row[playerIndex - 1]) existingNames.set(row[playerIndex - 1], i + 2);
    inGuildStatus.set(row[playerIndex - 1], row[inGuildIndex - 1]);
  });

  // Get last info board row+2
  var lastLRow = lastRow;
  for (var i = data.length - 1; i >= 0; i--) {
    if (String(data[i][11]).trim() !== "") { // Column L (index 12 - 1)
      lastLRow = i + 2;
      break;
    }
  }
  var deleteThreshold = lastLRow + 2; // The last row can be deleted

  // Variables for fetch
  var guildId = "k0TF-1dGQLSBmWqusGHBHQ";

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
      msgLogger(`HTTP response code ${response.getResponseCode()}.`, "e");
      return;
    }

    var fetchedData = JSON.parse(response.getContentText());
    if (!fetchedData || fetchedData.length === 0) {
      msgLogger(`No data received from API.`, "e");
      return;
    }
    msgLogger(`Successfully fetched member list!`);
  } catch (error) {
    msgLogger(`Error during member list fetch: ${error}.`, "e");
    return;
  }

  var newNames = new Set(fetchedData.map(player => player.Name));

  // Identify new players
  var newEntries = [...newNames].filter(name => !existingNames.has(name));

  // Identify last player in guild
  var lastYesRow = 2;
  data.forEach((row, i) => {
    if (row[inGuildIndex - 1] === inGuildYes) lastYesRow = i + 2;
  });

  var today = new Date();
  var commentDate = Utilities.formatDate(today, "UTC", "dd/MM/yy");

  // Step 1: Check existing members' guild status
  var guildMembers = new Set(fetchedData.map(player => player.Name));
  data.forEach((row, i) => {
    var playerName = row[playerIndex - 1];
    var currentGuildStatus = row[inGuildIndex - 1];
    
    // If the player is no longer in the guild, update the "In Guild" column
    if (playerName && !guildMembers.has(playerName) && currentGuildStatus !== inGuildNo) {
      sheet.getRange(i + 2, inGuildIndex).setValue(inGuildNo);
      sheet.getRange(i + 2, commentIndex).setValue(`${commentDate} player left guild checked by bot.`);  // Add comment
      msgLogger(`"${playerName}" no longer in guild, updated in-guild status to "${inGuildNo}".`);
    }
  });

  // Step 2: Insert new players
  if (newEntries.length > 0) {
    newEntries.forEach(newName => {
      var newRowIndex = lastYesRow + 1;
      sheet.insertRowAfter(lastYesRow);
      sheet.getRange(lastYesRow + 1, playerIndex).setValue(newName);
      sheet.getRange(lastYesRow + 1, inGuildIndex).setValue(inGuildYes);
      sheet.getRange(lastYesRow + 1, commentIndex).setValue(`${commentDate} new guild player added by bot.`);

      // Copy formula from previous row and apply to new row in "Fight Role"
      var prevFormula = sheet.getRange(lastYesRow, inFightRoleIndex).getFormula();
      if (prevFormula) {
        var updatedFormula = prevFormula.replace(/(\$?[A-Z])\d+/g, `$1${newRowIndex}`);
        sheet.getRange(newRowIndex, inFightRoleIndex).setFormula(updatedFormula);
      }
      
      lastYesRow++;
    });
  }

  // Step 3: Sort table before deletion
  if (sheet.getFilter()) {
    sheet.getFilter().sort(1, true).sort(2, false);
    msgLogger(`Successfully sorted the table.`);
  } else {
    msgLogger(`No existing filter found.`, "e");
  }

  // Re-read table before deletion
  lastRow = sheet.getMaxRows();
  dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol);
  data = dataRange.getValues();

  // Step 4: Delete old players and empty rows
  for (var i = lastRow - 1; i >= 1; i--) {
    var playerName = (data[i - 1] && data[i - 1][playerIndex - 1]) ? String(data[i - 1][playerIndex - 1]).trim() : "";
    var currentStatus = data[i - 1][inGuildIndex - 1];
    var past7Data = data[i - 1][past7Index - 1];
    var past14Data = data[i - 1][past14Index - 1];
    var past28Data = data[i - 1][past28Index - 1];
    var markData = data[i - 1][markIndex - 1];

    if (currentStatus === inGuildNo && 
        String(past7Data).trim() === noDataString && 
        String(past14Data).trim() === noDataString && 
        String(past28Data).trim() === noDataString &&
        String(markData).trim() === "") {
      if (i + 1 > deleteThreshold) { 
        sheet.deleteRow(i + 1);
        msgLogger(`Deleted one row for inactive player: "${playerName}".`);
      } else {
      sheet.getRange(i + 1, 1, 1, filterColumnCount).clearContent();
        msgLogger(`This row contains info card. Only cleared content for columns with filter: "${playerName}".`);
      }
      continue;
    }

    if (!playerName && i + 1 > deleteThreshold) {
      sheet.deleteRow(i + 1);
      msgLogger(`Deleted one empty row.`);
    }
  }

  // Save updated timestamp
  var searchText = "Player List Updated";
  var values = sheet.getDataRange().getValues().flat();
  var index = values.findIndex(text => typeof text === "string" && text.startsWith(searchText + ":"));
  
  if (index !== -1) {
    var rowIndex = Math.floor(index / lastCol) + 1;
    var colIndex = (index % lastCol) + 2;
    sheet.getRange(rowIndex, colIndex).setValue(Utilities.formatDate(new Date(), "UTC", "dd/MM/yyyy HH:mm"));
    msgLogger(`"${searchText}" timestamp saved at row ${rowIndex}, col ${colIndex}.`);
  } else {
    msgLogger(`"${searchText}" not found in sheet.`, "e");
  }

  msgLogger(`Member list updated!`);
}

/**
 * Log messages with timestamps and different severity levels.
 * If level is "e", logs as error.
 * If level is "w", logs as warning.
 * If level is omitted, logs as info.
 * @param {string} message - The message to log.
 * @param {string} [level] - The severity level.
 */
function msgLogger(message, level) {
  var now = new Date();
  var timeZone = Session.getScriptTimeZone();
  var timestamp = Utilities.formatDate(now, timeZone, "yyyy/MM/dd HH:mm:ss");

  var prefix = "Info";
  if (level === "e") {
    prefix = "Error";
  } else if (level === "w") {
    prefix = "Warn";
  }

  Logger.log(`${timestamp} [${prefix}] ${message}`);
}
