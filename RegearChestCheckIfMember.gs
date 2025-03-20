/*----- ----- ----- -----*/
// RegearChestCheckIfMember.gs
// For Albion Online "Tang Yuan" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/19
// Update Date: 2025/03/21
// Version: v1.2
/*----- ----- ----- -----*/

function regearChestCheckIfMember() {
  // Variables for user
  var sheetName = "FS ISLAND";
  //var sheetName = "Copy of FS ISLAND";
  var inGuildYes = "Yes";
  var inGuildNo = "No";

  // Member List Variables
  var sheetIdMemberList = "1KsGoAs1y-Yu8EvefVExg5XDTXOS2ngwl88eYu0m4NjQ";
  var sheetNameMemberList = "Master";
  
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) {
    msgLogger(`Sheet "${sheetName}" not found.`, "e");
    return;
  }

  var lastCol = sheet.getLastColumn();
  var lastRow = sheet.getLastRow();

  var sheetMemberList = SpreadsheetApp.openById(sheetIdMemberList).getSheetByName(sheetNameMemberList);
  if (!sheetMemberList) {
    msgLogger(`Sheet "${sheetNameMemberList}" not found in the target spreadsheet: "${sheetIdMemberList}".`, "e");
    return;
  }
  msgLogger(`Successfully load required sheet "${sheetNameMemberList}" in spreadsheet "${sheetIdMemberList}".`);
  
  // Read member list
  var dataMemberList = sheetMemberList.getRange("A2:B").getValues();
  var memberList = new Set();
  
  // Only include players in guild
  dataMemberList.forEach(row => {
    if (row[1] === inGuildYes) {
      memberList.add(row[0].trim());
    }
  });
  
  // Read regear chest player data
  var dataRange = sheet.getDataRange();
  var data = dataRange.getValues();
  var colors = dataRange.getBackgrounds();

  // *Only use lowercase color code only*
  var roleColorMap = {
    "#ea9999": "DPS",         // Red
    "#b6d7a8": "Healer",      // Green
    "#a4c2f4": "Tank",        // Blue
    "#b4a7d6": "Support",     // Purple
    "#efefef": "Extra",       // White
    "#f9cb9c": "Mega BS",     // Orange
    "#95fdff": "Boom BS",     // Cyan
    "#ffe599": "6oo BS",      // Yellow
    "#d5a6bd": "Jennie BS",   // Light Purple
    "#d9d9d9": "Core",        // Light Gray
    "#b7b7b7": "Battlemount", // Dark Gray
    "#ffbce3": "Officer"      // Pink
  };

  // Suffixes
  var suffixes = {
    suffixLeftGuild:    " (Left)",        // Player left the guild
    suffixSortErrorTop: " (ShouldAtBot)", // Player should be at the bottom
    suffixSortErrorBot: " (ShouldAtTop)"  // Player should be at the top
  };

  // Helper function: Clean player names from suffixes
  function cleanPlayerName(playerName) {
    // Escape special characters for use in regex
    var regexPattern = new RegExp(`\\s*(${Object.values(suffixes).map(suffix => suffix.replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1")).join("|")})`, "g");

    // Remove the suffixes if they exist
    return playerName.replace(regexPattern, "").trim();
  }

  // Helper function: Case-insensitive matching and name correction
  function getCorrectCaseName(playerName) {
    // Iterate through the guild member list to find a match
    for (var member of memberList) {
      if (member.toLowerCase() === playerName.toLowerCase()) {
        // Return the correctly cased name
        return member;
      }
    }
    // If no match is found, return the original name
    return playerName;
  }

  // Helper function: Fuzzy color matching with roleColorMap colors
  function isColorMatch(color, cellPosition = null) {
    var tolerance = 20;
    var cellName = (cellPosition && cellPosition.row !== undefined && cellPosition.col !== undefined) 
                  ? `${getCellName(cellPosition.row, cellPosition.col)}` : null;
    // If the color is invalid (undefined or empty), return false
    if (!color || typeof color !== "string" || !/^#[0-9A-Fa-f]{6}$/.test(color)) {
      msgLogger(`Invalid color detected: ${cellName ? `Cell ${cellName}` : `Unknown cell`} with color "${color}".`, "e");
      return false;
    } else if (color === "#ffffff") {
      //msgLogger(`Background color no set: ${cellName ? `Cell ${cellName}` : `Unknown cell`} with color "${color}".`, "w");
      return false;
    }

    // Convert hex color to RGB
    function hexToRgb(hex) {
      var r = parseInt(hex.slice(1, 3), 16);
      var g = parseInt(hex.slice(3, 5), 16);
      var b = parseInt(hex.slice(5, 7), 16);
      return { r, g, b };
    }
    
    var colorRgb = hexToRgb(color);
    for (var roleColor in roleColorMap) {
      var roleColorRgb = hexToRgb(roleColor);
      // Calculate color difference
      var diff = Math.abs(colorRgb.r - roleColorRgb.r) + Math.abs(colorRgb.g - roleColorRgb.g) + Math.abs(colorRgb.b - roleColorRgb.b);
      if (diff <= tolerance) {
        msgLogger(`Fuzzy color matched: ${cellName ? `Cell ${cellName}` : `Unknown cell`} "${color}" with role color ${roleColor}.`);
        return true; // Matched with one of the role colors
      }
    }
    msgLogger(`Fuzzy color mismatched: ${cellName ? `Cell ${cellName}` : `Unknown cell`} "${color}" with role color ${roleColor}.`);
    return false; // No match
  }

  // Step 1: Check player list area
  var pairTop = "TOP";
  var pairBot = "BOTTOM";
  var topBottomPairs = [];
  var numberAreas = new Set();
  var playerRows = new Set();

  for (var row = 0; row < data.length; row++) {
    for (var col = 0; col < data[row].length - 1; col++) {
      var cellValue = data[row][col]?.trim();
      var rightCellValue = data[row][col + 1]?.trim();

      if (cellValue === pairTop && rightCellValue === pairBot) {
      var bottomRow = row;
      while (++bottomRow < data.length && !data[bottomRow][col]?.trim());
      topBottomPairs.push({ start: row, end: bottomRow, col: col });
      }

      if (col === 1 && /^\d+(-\d+)?$/.test(cellValue)) {
        numberAreas.add(row);
      }
    }
  }
  topBottomPairs.forEach(({ start, end }) => {
    for (var row = start + 1; row < end; row++) { 
      if (numberAreas.has(row)) {
        playerRows.add(row);
      }
    }
  });

  numberAreas.forEach(row => {
    var isInsideAnyPair = topBottomPairs.some(({ start, end }) => row > start && row < end);
    if (!isInsideAnyPair) {
      playerRows.add(row);
    }
  });

  msgLogger(`Detected ${topBottomPairs.length} regear houses (TOP-BOTTOM pairs) with ${playerRows.size} chests, and total length is ${numberAreas.size}.`);

  // Step 2: Check player names
  for (var row of playerRows) {
    for (var col = 0; col < data[row].length; col++) {
      var cellColor = colors[row][col] ? colors[row][col].toLowerCase() : null;
      var nextCellColor = colors[row][col + 1] ? colors[row][col + 1].toLowerCase() : null;
      var playerName = data[row][col]?.trim();

      if (roleColorMap[cellColor] || (roleColorMap[cellColor] === undefined && isColorMatch(cellColor, { row: row, col: col }))) {
        if (!(roleColorMap[nextCellColor] || (roleColorMap[nextCellColor] === undefined && isColorMatch(nextCellColor, { row: row, col: col + 1 })))) {
          msgLogger(`Cell ${getCellName(row, col + 1)} doesn't contain a valid background color.`, "w");
        }

        // Clean the player name suffixes before processing
        playerName = cleanPlayerName(playerName);
        var nextPlayerName = col + 1 < data[row].length ? cleanPlayerName(data[row][col + 1]?.trim()) : null; // Next player name
        if (nextPlayerName) {
          nextPlayerName = cleanPlayerName(nextPlayerName);
        }

        // Check if player is in the guild list (case-insensitive), and automatically correct the case
        playerName = getCorrectCaseName(playerName);  // **Added this line for case correction**
        if (nextPlayerName) {
          nextPlayerName = getCorrectCaseName(nextPlayerName);  // **Added this line for case correction**
        }

        // Check if the players is in the member list. If not, append " (Left)"
        if (playerName && !memberList.has(playerName)) {
          msgLogger(`Cell ${getCellName(row, col)} player "${playerName}" left guild.`);
          playerName += suffixes.suffixLeftGuild;
        }
        if (nextPlayerName && !memberList.has(nextPlayerName)) {
          msgLogger(`Cell ${getCellName(row, col + 1)} player "${nextPlayerName}" left guild.`);
          nextPlayerName += suffixes.suffixLeftGuild;
        }

        // Check the order between current and next player
        if (nextPlayerName) {
          if (playerName > nextPlayerName) {
            msgLogger(`Sort error: Cell ${getCellName(row, col)} "${cleanPlayerName(playerName)}" & cell ${getCellName(row, col + 1)} "${cleanPlayerName(nextPlayerName)}".`);
            playerName += suffixes.suffixSortErrorTop;
            nextPlayerName += suffixes.suffixSortErrorBot;
          }
        }

        // Ensure left cell doesn't have empty while right cell has a player
        if (!playerName && nextPlayerName) {
          msgLogger(`Sort error: empty cell ${getCellName(row, col)} & cell ${getCellName(row, col + 1)} "${cleanPlayerName(nextPlayerName)}".`);
          nextPlayerName += suffixes.suffixSortErrorBot;
        }

        // Modify the data array directly
        data[row][col] = playerName;
        if (nextPlayerName) {
          data[row][col + 1] = nextPlayerName;
        }
        col++; 
      }
    }
  }

  // Step 3: Write the modified data back to the sheet
  dataRange.setValues(data);

  // Save updated timestamp
  var searchText = "Last member check";
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

  msgLogger(`Member list checked!`);
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

/**
 * Converts a column index (1-based) into a column letter, e.g. [0] -> A, [1] -> B, [26] -> AA, ...
 * @param {number} column - The column index.
 * @returns {string} The corresponding column letter.
 */
function columnIndexToLetter(column) {
  var letter = "";
  column++;
  while (column > 0) {
    var mod = (column - 1) % 26; // Get remainder (0-based index)
    letter = String.fromCharCode(65 + mod) + letter; // Convert to ASCII letter
    column = Math.floor((column - 1) / 26); // Move to the next place value
  }
  return letter;
}

/**
 * Converts a row index and column index into an A1 notation cell reference, e.g. [0,0] -> A1, [0,1] -> B1, [9,2] -> C10, ...
 * @param {number} row - The row index.
 * @param {number} column - The column index.
 * @returns {string} The corresponding A1 notation cell reference.
 */
function getCellName(row, col) {
  return columnIndexToLetter(col) + (row + 1);
}
