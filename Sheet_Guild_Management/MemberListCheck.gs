/*----- ----- ----- -----*/
// MemberListCheck.gs
// For Albion Online "Malicious Crew" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/04/16
// Version: v4.5
/*----- ----- ----- -----*/

function memberListCheck() {
  // Helper Function: Automatically select the sheet (prefer "Copy of ..." if available)
  function getTargetSheet(sheetBaseName) {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheets = spreadsheet.getSheets();
    const copySheet = sheets.find(sheet => sheet.getName().includes(`Copy of ${sheetBaseName}`));
    return copySheet || spreadsheet.getSheetByName(sheetBaseName);
  }

  // Variables for user
  const sheetName = "Master";
  const forceMarkInGuild = "Guild member";
  const forceMarkNotInGuild = "Not guild member (Force mark)";
  const inGuildYes = ["MC", "TY"];
  const inGuildNo = "❌";
  const noDataString = "No data";

  // Variables
  const sheet = getTargetSheet(sheetName);
  if (!sheet) {
    msgLogger(`Sheet "${sheetName}" not found.`, "e");
    return;
  }
  const lastCol = sheet.getLastColumn();
  let lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    msgLogger(`Sheet "${sheetName}" doesn't have enough rows (need >= 2).`, "e");
    return;
  }
  
  // Get column indexes based on column titles
  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  const columnNames = ["Player", "Guild", "Fight Role", "Past 7 Days", "Past 14 Days", "Past 28 Days", "Comment", "Force Mark"];
  const indexes = columnNames.map(name => headers.indexOf(name) + 1);

  // Check if any required column is missing
  if (indexes.includes(0)) {
    msgLogger(`Missing required columns: ${columnNames.filter((_, i) => indexes[i] === 0).join(", ")}.`, "e");
    return;
  }

  // Extract individual column indexes
  const [playerIndex, guildIndex, inFightRoleIndex, past7Index, past14Index, past28Index, commentIndex, markIndex] = indexes;
  
  // Read existing data efficiently
  const dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol);
  let data = dataRange.getValues();

  const existingNames = new Map();
  const inGuildStatus = new Map();
  
  if (!data || data.length === 0) {
    msgLogger(`No data retrieved from the sheet "${sheetName}".`, "e");
    return;
  }

  data.forEach((row, i) => {
    const name = row[playerIndex - 1];
    if (name) existingNames.set(row[playerIndex - 1], i + 2);
    inGuildStatus.set(row[playerIndex - 1], row[guildIndex - 1]);
  });

  // Get last info board row+2
  let lastLRow = lastRow;
  for (let i = data.length - 1; i >= 0; i--) {
    if (String(data[i][11]).trim() !== "") { // Column L (index 12 - 1)
      lastLRow = i + 2;
      break;
    }
  }
  const deleteThreshold = lastLRow + 2; // The last row can be deleted

  // Variables for fetch
  const guildIds = {
    "59YXPiViQdWXaARvPNyvMA": "MC", //"Malicious Crew"
    "k0TF-1dGQLSBmWqusGHBHQ": "TY"  //"Tang Yuan"
    };
  const guildMembers = new Map();
  const newNames = new Set();

  // Fetch guild members from API
  for (const guildId in guildIds) {
    const url = `https://gameinfo-sgp.albiononline.com/api/gameinfo/guilds/${guildId}/members`;
    const options = {
      "method": "GET",
      "headers": { "Accept": "application/json, text/plain, */*" },
      "muteHttpExceptions": true
      };

    try {
      const response = UrlFetchApp.fetch(url, options);
      if (response.getResponseCode() !== 200) {
        msgLogger(`HTTP response code ${response.getResponseCode()} for guild "${guildIds[guildId]}".`, "e");
        return;
      }

      const fetchedData = JSON.parse(response.getContentText());
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
  const newEntries = [...newNames].filter(name => !existingNames.has(name));

  // Identify last player in guild
  let lastYesRow = 2;
  data.forEach((row, i) => {
    if (inGuildYes.includes(row[guildIndex - 1])) lastYesRow = i + 2;
  });

  const today = new Date();
  const commentDate = Utilities.formatDate(today, "UTC", "dd/MM/yy");

  // Step 1: Check existing members' guild status in bulk
  const updatesGuild = [], updatesComment = [];

  data.forEach((row, i) => {
    const playerName = row[playerIndex - 1];
    const currentGuildStatus = row[guildIndex - 1];
    const mark = row[markIndex - 1];
    if (playerName) {
      // If force marked as not guild member
      if (mark === forceMarkNotInGuild) {
        updatesGuild.push([inGuildNo]);
        updatesComment.push([`${commentDate} forced mark as not in guild.`]);
        msgLogger(`"${playerName}" forced mark as not in guild, updated in-guild status to "${inGuildNo}".`);
      }
      // If force marked as guild member
      else if (mark.startsWith(forceMarkInGuild)) { 
          const matchedGuild = mark.match(/Guild member - (\w+) \(Force mark\)/); 
          if (matchedGuild) {
              var forcedGuild = matchedGuild[1];
              updatesGuild.push([forcedGuild]);
              updatesComment.push([`${commentDate} forced mark as in guild "${forcedGuild}".`]);
              msgLogger(`"${playerName}" forced mark as in guild "${forcedGuild}", updated in-guild status to "${forcedGuild}".`);
          } else {
              updatesGuild.push([currentGuildStatus]);
              updatesComment.push([`${commentDate} wrong forced mark tag.`]);
              msgLogger(`"${playerName}" has wrong forced mark.`, "w");
          }
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
      const newRowIndex = lastYesRow + 1;
      sheet.insertRowAfter(lastYesRow);
      sheet.getRange(lastYesRow + 1, playerIndex).setValue(newName);
      sheet.getRange(lastYesRow + 1, guildIndex).setValue(guildMembers.get(newName));
      sheet.getRange(lastYesRow + 1, commentIndex).setValue(`${commentDate} new ${guildMembers.get(newName)} guild player added by bot.`);
      msgLogger(`"${guildMembers.get(newName)} guild new player "${newName}" added by bot.`);

      // Copy formula from previous row and apply to new row in "Fight Role"
      const prevFormula = sheet.getRange(lastYesRow, inFightRoleIndex).getFormula();
      if (prevFormula) {
        const updatedFormula = prevFormula.replace(/(\$?[A-Z])\d+/g, `$1${newRowIndex}`);
        sheet.getRange(newRowIndex, inFightRoleIndex).setFormula(updatedFormula);
      }
      
      lastYesRow++;
    });
  }

  // Step 4: Sort table before deletion
  let filterColumnCount = lastCol;
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
  for (let i = lastRow - 1; i >= 1; i--) {
    const playerName = (data[i - 1] && data[i - 1][playerIndex - 1]) ? String(data[i - 1][playerIndex - 1]).trim() : "";
    const currentStatus = data[i - 1][guildIndex - 1];
    const past7Data = data[i - 1][past7Index - 1];
    const past14Data = data[i - 1][past14Index - 1];
    const past28Data = data[i - 1][past28Index - 1];
    const markData = data[i - 1][markIndex - 1];

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
  const searchText = "Player List Updated";
  const values = sheet.getDataRange().getValues().flat();
  const index = values.findIndex(text => typeof text === "string" && text.startsWith(searchText + ":"));
  
  if (index !== -1) {
    const rowIndex = Math.floor(index / lastCol) + 1;
    const colIndex = (index % lastCol) + 2;
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
  const now = new Date();
  const timeZone = Session.getScriptTimeZone();
  const timestamp = Utilities.formatDate(now, timeZone, "yyyy/MM/dd HH:mm:ss");

  let prefix = "Info";
  if (level === "e") {
    prefix = "Error";
  } else if (level === "w") {
    prefix = "Warn";
  }

  Logger.log(`${timestamp} [${prefix}] ${message}`);
}
