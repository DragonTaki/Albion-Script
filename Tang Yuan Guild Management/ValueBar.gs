/*----- ----- ----- -----*/
// ValueBar.gs
// For Albion Online "Tang Yuan" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/12
// Update Date: 2025/03/12
// Version: v1.0
/*----- ----- ----- -----*/

function increaseL10() {
  adjustValue("L10", 1);
}

function decreaseL10() {
  adjustValue("L10", -1);
}

function increaseL11() {
  adjustValue("L11", 1);
}

function decreaseL11() {
  adjustValue("L11", -1);
}

function increaseL12() {
  adjustValue("L12", 1);
}

function decreaseL12() {
  adjustValue("L12", -1);
}

function adjustValue(cellAddress, change) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var cell = sheet.getRange(cellAddress);
  var currentValue = cell.getValue();
  var maximum = 50;
  var minimum = 0;

  // If not number, set to 0
  if (typeof currentValue !== "number") {
    currentValue = 0;
  }

  var newValue = currentValue + change;
  if (newValue > maximum) newValue = maximum;
  if (newValue < minimum) newValue = minimum;

  cell.setValue(newValue);
}
