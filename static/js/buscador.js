function searchTable() {
    const input = document.getElementById('search').value.toLowerCase();
    const rows = document.querySelectorAll('#tableBody tr');
    
    if (input === "") {
      // Si el buscador está vacío, se muestran todas las filas que no sean paneles y se ocultan los paneles.
      rows.forEach(row => {
        if (row.classList.contains('panel')) {
          row.style.display = 'none';
        } else {
          row.style.display = '';
        }
      });
      return;
    }
    
    // Si hay texto en el buscador, se filtran los renglones
    rows.forEach(row => {
      const cells = row.querySelectorAll('td');
      let match = Array.from(cells).some(cell => cell.textContent.toLowerCase().includes(input));
      row.style.display = match ? '' : 'none';
      // Si el renglón es un panel y hay coincidencia, aseguramos que la fila anterior (el encabezado del acordeón) esté visible
      if (match && row.classList.contains('panel')) {
        const previousRow = row.previousElementSibling;
        if (previousRow) previousRow.style.display = '';
      }
    });
  }
  
  document.querySelectorAll('.accordion').forEach(button => {
    button.addEventListener('click', function() {
      const panel = this.closest('tr').nextElementSibling;
      panel.style.display = (panel.style.display === 'table-row') ? 'none' : 'table-row';
    });
  });
  
  // Ejecutar la búsqueda en cada pulsación de tecla en el input de búsqueda
  document.getElementById('search').addEventListener('keyup', searchTable);
  
  