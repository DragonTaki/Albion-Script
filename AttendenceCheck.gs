/*----- ----- ----- -----*/
// AttendanceCheck.gs
// For Albion Online "Tang Yuan" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/03/19
// Version: v3.2
/*----- ----- ----- -----*/

function attendanceCheck() {
  // Variables for user
  var sheetName = "Master";
  //var sheetName = "Copy of Master";
  var forceMark = ["Not guild member (Force mark)"];
  var inGuildYes = "Yes";
  var inGuildNo = "No";
  var attendanceNoData = "No data";

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  var lastCol = sheet.getLastColumn();
  var lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    Logger.log("Error: 'Master' tab doesn't have enough rows (need >= 2). ");
    return;
  }
  
  // Get column indexes based on column titles
  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var columnNames = ["Player", "In Guild", "Past 7 Days", "Past 14 Days", "Past 28 Days", "Comment", "Force Mark"];
  var indexes = columnNames.map(name => headers.indexOf(name) + 1);
  
  // Check if any required column is missing
  if (indexes.includes(0)) {
    Logger.log(`Error: Missing required columns: ${columnNames.filter((_, i) => indexes[i] === 0).join(", ")}`);
    return;
  }
  
  // Extract individual column indexes
  var [playerIndex, inGuildIndex, past7Index, past14Index, past28Index, commentIndex, markIndex] = indexes;
  
  // Read existing data in one go to minimize getRange calls
  var dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();

  // Variables for fetch
  var guildName = "Tang Yuan";
  var intervals = [7, 14, 28];
  var minGP = 50;
  var fetchedData = {};

  // Fetch attendance data for each interval, and store in Map for fast lookup
  intervals.forEach(interval => {
    var url = `https://api-east.albionbattles.com/player?guildSearch=${encodeURIComponent(guildName)}&interval=${interval}&minGP=${minGP}`;
    var options = {
      "method": "GET",
      "headers": { "Accept": "application/json" },
        "muteHttpExceptions": true
      };
    
    try {
      var response = UrlFetchApp.fetch(url, options);
      if (response.getResponseCode() !== 200) {
        Logger.log(`Error: HTTP response code ${response.getResponseCode()}`);
        return;
      }
      var data = JSON.parse(response.getContentText());
      if (!Array.isArray(data)) {
        Logger.log(`Invalid response format: ${JSON.stringify(data)}`);
        return;
      }
      fetchedData[interval] = new Map(data.map(player => [player.name, player.battleNumber || 0]));
      Logger.log(`Successfully fetched attendance data for ${interval} days.`);
    } catch (error) {
      Logger.log(`Error fetching attendance: ${error}`);
    }
  });

  // Process each player and update attendance records in bulk
  var results7Days = [], results14Days = [], results28Days = [];
  
  dataRange.forEach((row, i) => {
    var playerName = row[playerIndex - 1];
    var playerStatus = row[inGuildIndex - 1];
    var mark = row[markIndex - 1];
    if (!playerName) return;
    
    if (forceMark.includes(mark)) {
      row[inGuildIndex - 1] = inGuildNo;
      playerStatus = inGuildNo;
    }

    results7Days[i] = playerStatus === inGuildNo ? attendanceNoData : (fetchedData[7]?.get(playerName) || 0);
    results14Days[i] = playerStatus === inGuildNo ? attendanceNoData : (fetchedData[14]?.get(playerName) || 0);
    results28Days[i] = playerStatus === inGuildNo ? attendanceNoData : (fetchedData[28]?.get(playerName) || 0);
  });

  // Batch update attendance data
  sheet.getRange(2, past7Index, lastRow - 1).setValues(results7Days.map(v => [v]));
  sheet.getRange(2, past14Index, lastRow - 1).setValues(results14Days.map(v => [v]));
  sheet.getRange(2, past28Index, lastRow - 1).setValues(results28Days.map(v => [v]));
  
  // Update timestamp
  var searchText = "Attendance Updated:";
  var values = sheet.getDataRange().getValues().flat();
  var index = values.indexOf(searchText);
  
  if (index !== -1) {
    var rowIndex = Math.floor(index / lastCol) + 1;
    var colIndex = (index % lastCol) + 2;
    sheet.getRange(rowIndex, colIndex).setValue(Utilities.formatDate(new Date(), "UTC", "dd/MM/yyyy HH:mm"));
    Logger.log("'Attendance Updated' timestamp saved at row " + rowIndex + ", col " + colIndex);
  } else {
    Logger.log(`Error: "${searchText}" not found in sheet.`);
  }
  
  Logger.log("Attendance data saved!");
}
