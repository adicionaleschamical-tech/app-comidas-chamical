var SHEET_ID = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA";

function doGet(e) {
  var action = e.parameter.accion;
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName("PEDIDOS"); 

  if (action == "nuevo") {
    try {
      sheet.appendRow([
        new Date(), 
        "'" + e.parameter.tel, // El apostrofe evita que Google borre ceros a la izquierda
        e.parameter.nombre, 
        e.parameter.dir, 
        e.parameter.detalle, 
        e.parameter.total, 
        "Pendiente"
      ]);
      return ContentService.createTextOutput("OK");
    } catch (err) {
      return ContentService.createTextOutput("Error: " + err.message);
    }
  }
  return ContentService.createTextOutput("Script funcionando");
}
