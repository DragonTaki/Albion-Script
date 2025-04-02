/*----- ----- ----- -----*/
// MemberListCheck.gs
// For Albion Online "Malicious Crew" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/04/02
// Version: v4.2
/*----- ----- ----- -----*/

function memberListCheck() {
  // Variables for user
  var sheetName = "Master";
  //var sheetName = "Copy of Master";
  var forceMarkNotInGuild = "Not guild member (Force mark)";
  var inGuildYes = ["MC", "TY"];
  var inGuildNo = "❌";
  var noDataString = "No data";

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) {
    msgLogger(`Sheet "${sheetName}" not found.`, "e");
    return;
  }
  var lastCol = sheet.getLastColumn();
  var lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    msgLogger(`Sheet "${sheetName}" doesn't have enough rows (need >= 2).`, "e");
    return;
  }
  
  // Get column indexes based on column titles
  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var columnNames = ["Player", "Guild", "Fight Role", "Past 7 Days", "Past 14 Days", "Past 28 Days", "Comment", "Force Mark"];
  var indexes = columnNames.map(name => headers.indexOf(name) + 1);

  // Check if any required column is missing
  if (indexes.includes(0)) {
    msgLogger(`Missing required columns: ${columnNames.filter((_, i) => indexes[i] === 0).join(", ")}.`, "e");
    return;
  }

  // Extract individual column indexes
  var [playerIndex, guildIndex, inFightRoleIndex, past7Index, past14Index, past28Index, commentIndex, markIndex] = indexes;
  
  // Read existing data efficiently
  var dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol);
  var data = dataRange.getValues();

  var existingNames = new Map();
  var inGuildStatus = new Map();
  
  if (!data || data.length === 0) {
    msgLogger(`No data retrieved from the sheet "${sheetName}".`, "e");
    return;
  }

  data.forEach((row, i) => {
    if (row[playerIndex - 1]) existingNames.set(row[playerIndex - 1], i + 2);
    inGuildStatus.set(row[playerIndex - 1], row[guildIndex - 1]);
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
  var guildIds = {
    "59YXPiViQdWXaARvPNyvMA": "MC", //"Malicious Crew"
    "k0TF-1dGQLSBmWqusGHBHQ": "TY"  //"Tang Yuan"
    };
  var guildMembers = new Map();
  var newNames = new Set();

  // Fetch guild members from API
  for (var guildId in guildIds) {
    var url = `https://gameinfo-sgp.albiononline.com/api/gameinfo/guilds/${guildId}/members`;
    var options = {
      "method": "GET",
      "headers": { "Accept": "application/json, text/plain, */*" },
      "muteHttpExceptions": true
      };

    try {
      var response = UrlFetchApp.fetch(url, options);
      if (response.getResponseCode() !== 200) {
        msgLogger(`HTTP response code ${response.getResponseCode()} for guild "${guildIds[guildId]}".`, "e");
        return;
      }

      var fetchedData = JSON.parse(response.getContentText());
      if (!fetchedData || fetchedData.length === 0) {
        msgLogger(`No data received from API for guild "${guildIds[guildId]}".`, "e");
        return;
      }

      fetchedData.forEach(player => {
        guildMembers.set(player.Name, guildIds[guildId]);
        newNames.add(player.Name);
      });

      msgLogger(`Successfully fetched member list for guild "${guildIds[guildId]}"!`);
    } catch (error) {
      msgLogger(`Error during member list fetch for guild "${guildIds[guildId]}": ${error}.`, "e");
      return;
    }
  }

  // Identify new players
  var newEntries = [...newNames].filter(name => !existingNames.has(name));

  // Identify last player in guild
  var lastYesRow = 2;
  data.forEach((row, i) => {
    if (inGuildYes.includes(row[guildIndex - 1])) lastYesRow = i + 2;
  });

  var today = new Date();
  var commentDate = Utilities.formatDate(today, "UTC", "dd/MM/yy");

  // Step 1: Check existing members' guild status in bulk
  var updatesGuild = [], updatesComment = [];

  data.forEach((row, i) => {
    var playerName = row[playerIndex - 1];
    var currentGuildStatus = row[guildIndex - 1];
    var mark = row[markIndex - 1];
    if (playerName) {
      // If force marked as not guild member
      if (currentGuildStatus !== inGuildNo && mark === forceMarkNotInGuild) {
        updatesGuild.push([inGuildNo]);
        updatesComment.push([`${commentDate} forced mark as not in guild.`]);
        msgLogger(`"${playerName}" forced mark as not in guild, updated in-guild status to "${inGuildNo}".`);
      }
      // If the player is no longer in the guild
      else if (!guildMembers.has(playerName) && currentGuildStatus !== inGuildNo) {
        updatesGuild.push([inGuildNo]);
        updatesComment.push([`${commentDate} player left guild "${currentGuildStatus}" checked by bot.`]);
        msgLogger(`"${playerName}" no longer in guild "${currentGuildStatus}", updated in-guild status to "${inGuildNo}".`);
      }
      // If the player switched the guild
      else if (guildMembers.has(playerName) && currentGuildStatus !== guildMembers.get(playerName)) {
        updatesGuild.push([guildMembers.get(playerName)]);
        updatesComment.push([`${commentDate} player switch guild from "${currentGuildStatus}" to "${guildMembers.get(playerName)}" checked by bot.`]);
        msgLogger(`"${playerName}" switch guild from "${currentGuildStatus}" to "${guildMembers.get(playerName)}", updated in-guild status to "${guildMembers.get(playerName)}".`);
      }
      // Nothing changed
      else {
        updatesGuild.push([currentGuildStatus]);
        updatesComment.push([row[commentIndex - 1]]);
      }
    } else {
      updatesGuild.push([""]);
      updatesComment.push([""]);
    }
  });

  // Step 2: Batch update guild status data
  sheet.getRange(2, guildIndex, data.length, 1).setValues(updatesGuild);
  sheet.getRange(2, commentIndex, data.length, 1).setValues(updatesComment);

  // Step 3: Insert new players
  if (newEntries.length > 0) {
    newEntries.forEach(newName => {
      var newRowIndex = lastYesRow + 1;
      sheet.insertRowAfter(lastYesRow);
      sheet.getRange(lastYesRow + 1, playerIndex).setValue(newName);
      sheet.getRange(lastYesRow + 1, guildIndex).setValue(guildMembers.get(newName));
      sheet.getRange(lastYesRow + 1, commentIndex).setValue(`${commentDate} new ${guildMembers.get(newName)} guild player added by bot.`);
      msgLogger(`"${guildMembers.get(newName)} guild new player "${newName}" added by bot.`);

      // Copy formula from previous row and apply to new row in "Fight Role"
      var prevFormula = sheet.getRange(lastYesRow, inFightRoleIndex).getFormula();
      if (prevFormula) {
        var updatedFormula = prevFormula.replace(/(\$?[A-Z])\d+/g, `$1${newRowIndex}`);
        sheet.getRange(newRowIndex, inFightRoleIndex).setFormula(updatedFormula);
      }
      
      lastYesRow++;
    });
  }

  // Step 4: Sort table before deletion
  var filterColumnCount = lastCol;
  if (sheet.getFilter()) {
    filterColumnCount = sheet.getFilter().getRange().getLastColumn();
    sheet.getFilter().sort(1, true).sort(2, false);
    msgLogger(`Successfully sorted the table.`);
  } else {
    msgLogger(`No existing filter found.`, "e");
  }

  // Re-read table before deletion
  lastRow = sheet.getMaxRows();
  dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol);
  data = dataRange.getValues();

  // Step 5: Delete old players and empty rows
  for (var i = lastRow - 1; i >= 1; i--) {
    var playerName = (data[i - 1] && data[i - 1][playerIndex - 1]) ? String(data[i - 1][playerIndex - 1]).trim() : "";
    var currentStatus = data[i - 1][guildIndex - 1];
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
