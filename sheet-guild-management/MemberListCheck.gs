/*----- ----- ----- -----*/
// MemberListCheck.gs
// For Albion Online "Malicious Crew" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/04/17
// Version: v5.0
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
  const SHEET_NAME = "Master";
  const FORCE_MARK_IN_GUILD = "Guild member";
  const FORCE_MARK_NOT_IN_GUILD = "Not guild member (Force mark)";
  const GUILD_TAGS = ["MC", "TY"];
  const NOT_IN_GUILD_MARK = "❌";
  const NO_DATA_STRING = "No data";

  // Variables
  const sheet = getTargetSheet(SHEET_NAME);
  if (!sheet) {
    msgLogger(`Sheet "${SHEET_NAME}" not found.`, "e");
    return;
  }
  const lastColumn = sheet.getLastColumn();
  let lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    msgLogger(`Sheet "${SHEET_NAME}" doesn't have enough rows (need >= 2).`, "e");
    return;
  }

  // Read headers
  const headerRow = sheet.getRange(1, 1, 1, lastColumn).getValues()[0];
  
  // Define expected column titles
  const columnTitleMap = {
    player: "Player",
    guild: "Guild",
    fightRole: "Fight Role",
    past7: "Past 7 Days",
    past14: "Past 14 Days",
    past28: "Past 28 Days",
    joinedDate: "Joined Date",
    comment: "Comment",
    mark: "Force Mark"
  };
  let columns;
  
  // Check if any required column is missing
  try {
    columns = getColumnIndexes(headerRow, columnTitleMap);
  } catch (error) {
    return;
  }

  // Wrap columns to auto -1 when accessing by Proxy
  const columns_ = new Proxy(columns, {
    get: (target, prop) => target[prop] - 1
  });

  // Read existing data efficiently
  let dataRange = sheet.getRange(2, 1, lastRow - 1, lastColumn);
  let tableData = dataRange.getValues();

  const playerNameMap = new Map();
  const currentGuildMap = new Map();
  
  if (!tableData || tableData.length === 0) {
    msgLogger(`No data retrieved from the sheet "${SHEET_NAME}".`, "e");
    return;
  }

  tableData.forEach((row, i) => {
    const playerName = row[columns_.player];
    if (playerName) playerNameMap.set(playerName, i + 2);
    currentGuildMap.set(playerName, row[columns_.guild]);
  });

  // Get last info board row+2
  let lastInfoBoardRow = lastRow;
  for (let i = tableData.length - 1; i >= 0; i--) {
    if (String(tableData[i][11]).trim() !== "") { // Column L (index 12 - 1)
      lastInfoBoardRow = i + 2;
      break;
    }
  }
  const deleteThresholdRow = lastInfoBoardRow + 2; // The last row can be deleted

  // Variables for fetch
  const guildIdToTag = {
    "59YXPiViQdWXaARvPNyvMA": "MC", //"Malicious Crew"
    "k0TF-1dGQLSBmWqusGHBHQ": "TY"  //"Tang Yuan"
    };
  const guildMembersMap = new Map();
  const fetchedNamesSet = new Set();

  // Fetch guild members from API
  for (const guildId in guildIdToTag) {
    const url = `https://gameinfo-sgp.albiononline.com/api/gameinfo/guilds/${guildId}/members`;
    const options = {
      "method": "GET",
      "headers": { "Accept": "application/json, text/plain, */*" },
      "muteHttpExceptions": true
      };

    try {
      const response = UrlFetchApp.fetch(url, options);
      if (response.getResponseCode() !== 200) {
        msgLogger(`HTTP response code ${response.getResponseCode()} for guild "${guildIdToTag[guildId]}".`, "e");
        return;
      }

      const fetchedData = JSON.parse(response.getContentText());
      if (!fetchedData || fetchedData.length === 0) {
        msgLogger(`No data received from API for guild "${guildIdToTag[guildId]}".`, "e");
        return;
      }

      fetchedData.forEach(player => {
        guildMembersMap.set(player.Name, guildIdToTag[guildId]);
        fetchedNamesSet.add(player.Name);
      });

      msgLogger(`Successfully fetched member list for guild "${guildIdToTag[guildId]}"!`);
    } catch (error) {
      msgLogger(`Error during member list fetch for guild "${guildIdToTag[guildId]}": ${error}.`, "e");
      return;
    }
  }

  // Identify new players
  const newGuildMemberNames = [...fetchedNamesSet].filter(name => !playerNameMap.has(name));

  // Identify last player in guild
  let lastInGuildRowIndex = 2;
  tableData.forEach((row, i) => {
    if (GUILD_TAGS.includes(row[columns_.guild])) lastInGuildRowIndex = i + 2;
  });

  const today = new Date();
  const commentDateStr = Utilities.formatDate(today, "UTC", "dd/MM/yy");
  const joinedDateStr = Utilities.formatDate(today, "UTC", "dd/MM/yyyy");

  // Step 1: Check existing members' guild status in bulk
  const updatesGuild = [];
  const updatesComment = [];

  tableData.forEach((row, i) => {
    const playerName = row[columns_.player];
    const currentGuildStatus = row[columns_.guild];
    const currentMark = row[columns_.mark];
    if (playerName) {
      // If force marked as not guild member
      if (currentMark === FORCE_MARK_NOT_IN_GUILD) {
        updatesGuild.push([NOT_IN_GUILD_MARK]);
        updatesComment.push([`${commentDateStr} forced mark as not in guild.`]);
        msgLogger(`"${playerName}" forced mark as not in guild, updated in-guild status to "${NOT_IN_GUILD_MARK}".`);
      }
      // If force marked as guild member
      else if (currentMark.startsWith(FORCE_MARK_IN_GUILD)) { 
          const matchedGuild = currentMark.match(/Guild member - (\w+) \(Force mark\)/); 
          if (matchedGuild) {
              const forcedGuildTag = matchedGuild[1];
              updatesGuild.push([forcedGuildTag]);
              updatesComment.push([`${commentDateStr} forced mark as in guild "${forcedGuildTag}".`]);
              msgLogger(`"${playerName}" forced mark as in guild "${forcedGuildTag}", updated in-guild status to "${forcedGuildTag}".`);
          } else {
              updatesGuild.push([currentGuildStatus]);
              updatesComment.push([`${commentDateStr} wrong forced mark tag.`]);
              msgLogger(`"${playerName}" has wrong forced mark.`, "w");
          }
      }
      // If the player is no longer in the guild
      else if (!guildMembersMap.has(playerName) && currentGuildStatus !== NOT_IN_GUILD_MARK) {
        updatesGuild.push([NOT_IN_GUILD_MARK]);
        updatesComment.push([`${commentDateStr} player left guild "${currentGuildStatus}" checked by bot.`]);
        msgLogger(`"${playerName}" no longer in guild "${currentGuildStatus}", updated in-guild status to "${NOT_IN_GUILD_MARK}".`);
      }
      // If the player switched the guild
      else if (guildMembersMap.has(playerName) && currentGuildStatus !== guildMembersMap.get(playerName)) {
        updatesGuild.push([guildMembersMap.get(playerName)]);
        updatesComment.push([`${commentDateStr} player switch guild from "${currentGuildStatus}" to "${guildMembersMap.get(playerName)}" checked by bot.`]);
        msgLogger(`"${playerName}" switch guild from "${currentGuildStatus}" to "${guildMembersMap.get(playerName)}", updated in-guild status to "${guildMembersMap.get(playerName)}".`);
      }
      // Nothing changed
      else {
        updatesGuild.push([currentGuildStatus]);
        updatesComment.push([row[columns_.comment]]);
      }
    } else {
      updatesGuild.push([""]);
      updatesComment.push([""]);
    }
  });

  // Step 2: Batch update guild status data
  sheet.getRange(2, columns.guild, tableData.length, 1).setValues(updatesGuild);
  sheet.getRange(2, columns.comment, tableData.length, 1).setValues(updatesComment);

  // Step 3: Insert new players
  if (newGuildMemberNames.length > 0) {
    newGuildMemberNames.forEach(newName => {
      const newRowIndex = lastInGuildRowIndex + 1;
      sheet.insertRowAfter(lastInGuildRowIndex);
      sheet.getRange(newRowIndex, columns.player).setValue(newName);
      sheet.getRange(newRowIndex, columns.guild).setValue(guildMembersMap.get(newName));
      sheet.getRange(newRowIndex, columns.comment).setValue(`${commentDateStr} new ${guildMembersMap.get(newName)} guild player added by bot.`);
      sheet.getRange(newRowIndex, columns.joinedDate).setValue(joinedDateStr);
      msgLogger(`"${guildMembersMap.get(newName)} guild new player "${newName}" added by bot.`);

      // Copy formula from previous row and apply to new row in "Fight Role"
      const prevFormula = sheet.getRange(lastInGuildRowIndex, columns.fightRole).getFormula();
      if (prevFormula) {
        const updatedFormula = prevFormula.replace(/(\$?[A-Z])\d+/g, `$1${newRowIndex}`);
        sheet.getRange(newRowIndex, columns.fightRole).setFormula(updatedFormula);
      }
      
      lastInGuildRowIndex++;
    });
  }

  // Step 4: Sort table before deletion
  let filterColumnCount = lastColumn;
  if (sheet.getFilter()) {
    filterColumnCount = sheet.getFilter().getRange().getLastColumn();
    sheet.getFilter().sort(1, true).sort(2, false);
    msgLogger(`Successfully sorted the table.`);
  } else {
    msgLogger(`No existing filter found.`, "e");
  }

  // Re-read table before deletion
  lastRow = sheet.getMaxRows();
  dataRange = sheet.getRange(2, 1, lastRow - 1, lastColumn);
  tableData = dataRange.getValues();

  // Step 5: Delete old players and empty rows
  for (let i = lastRow - 1; i >= 1; i--) {
    const playerName = (tableData[i - 1] && tableData[i - 1][columns_.player]) ? String(tableData[i - 1][columns_.player]).trim() : "";
    const currentStatus = tableData[i - 1][columns_.guild];
    const past7Data = tableData[i - 1][columns_.past7];
    const past14Data = tableData[i - 1][columns_.past14];
    const past28Data = tableData[i - 1][columns_.past28];
    const markData = tableData[i - 1][columns_.mark];

    if (currentStatus === NOT_IN_GUILD_MARK && 
        String(past7Data).trim() === NO_DATA_STRING && 
        String(past14Data).trim() === NO_DATA_STRING && 
        String(past28Data).trim() === NO_DATA_STRING &&
        String(markData).trim() === "") {
      if (i + 1 > deleteThresholdRow) { 
        sheet.deleteRow(i + 1);
        msgLogger(`Deleted one row for inactive player: "${playerName}".`);
      } else {
      sheet.getRange(i + 1, 1, 1, filterColumnCount).clearContent();
        msgLogger(`This row contains info card. Only cleared content for columns with filter: "${playerName}".`);
      }
      continue;
    }

    if (!playerName && i + 1 > deleteThresholdRow) {
      sheet.deleteRow(i + 1);
      msgLogger(`Deleted one empty row.`);
    }
  }

  // Save updated timestamp
  const SEARCH_TEXT = "Player List Updated";
  const values = sheet.getDataRange().getValues().flat();
  const index = values.findIndex(text => typeof text === "string" && text.startsWith(SEARCH_TEXT + ":"));
  
  if (index !== -1) {
    const rowIndex = Math.floor(index / lastColumn) + 1;
    const colIndex = (index % lastColumn) + 2;
    sheet.getRange(rowIndex, colIndex).setValue(Utilities.formatDate(new Date(), "UTC", "dd/MM/yyyy HH:mm"));
    msgLogger(`"${SEARCH_TEXT}" timestamp saved at row ${rowIndex}, col ${colIndex}.`);
  } else {
    msgLogger(`"${SEARCH_TEXT}" not found in sheet.`, "e");
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

/**
 * Get indexes of specified column headers
 * @param {string[]} headers - The header row of the sheet
 * @param {Object} nameMap - Mapping of logical names to column titles
 * @returns {Object} - Object with logical names and their 1-based column indexes
 * @throws {Error} - Throws if required column headers are missing
 */
function getColumnIndexes(headers, nameMap) {
  const indexes = {};
  const missing = [];

  for (const key in nameMap) {
    const title = nameMap[key];
    const idx = headers.indexOf(title);
    if (idx === -1) {
      missing.push(title);
    } else {
      indexes[key] = idx + 1; // Convert 0-based to 1-based index
    }
  }

  if (missing.length > 0) {
    msgLogger(`Missing required columns: ${missing.join(", ")}`, "e");
    throw new Error(`Missing required columns.`);
  }

  return indexes;
}
