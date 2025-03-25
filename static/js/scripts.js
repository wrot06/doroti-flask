//1. contador de caracteres maxiomo hasta 394
const tituloEl = document.getElementById("titulo");
const charCountEl = document.getElementById("charCount");
const maxChars = 394;

tituloEl.addEventListener("input", () => {
  const len = tituloEl.value.length;
  if (len > maxChars) {
    tituloEl.value = tituloEl.value.slice(0, maxChars);
  }
  charCountEl.textContent = `${tituloEl.value.length} / ${maxChars}`;
});// Fin del script 1

//2. inicia el puntero en textarea titulo
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('titulo').focus();
});// Fin del script 2


//3. Esperar a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', () => {
  const tituloTextarea = document.getElementById('titulo');
  tituloTextarea.focus();

  tituloTextarea.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault(); // Evita el salto de línea
      const tituloValue = tituloTextarea.value.trim();
      if (tituloValue) {
        document.getElementById('paginaFinal').focus();
      }
    }
  });
});// Fin del script 3



//---------------------------------------------------------------
// 4. Agregar un nuevo Capítulo
$(document).ready(() => {
  // Obtener configuración desde el contenedor
  const config = $("#config");
  let siguientePagina = Number(config.data("pagina-siguiente"));
  const caja = Number(config.data("caja"));
  const carpeta = Number(config.data("carpeta"));
  const agregarCapituloURL = config.data("agregar-capitulo");

  if (typeof inicializarPaginas === "function") {
    inicializarPaginas();
  }

  // Elementos de la UI para agregar capítulo y actualizar información
  const $form = $("#capituloForm");
  const $tituloInput = $("#titulo");
  const $paginaFinalInput = $("#paginaFinal");
  const $capitulosTableBody = $("#capitulosTable tbody");
  const $ultimaPagina = $("#ultimaPagina");
  const $ultimaPagina1 = $("#ultimaPagina1");

  $form.on("submit", (event) => {
    event.preventDefault();

    // Validar que se haya seleccionado una etiqueta
    const etiquetaSeleccionada = $("input[name='etiqueta']:checked").val();
    if (!etiquetaSeleccionada) {
      alert("Por favor, selecciona una etiqueta antes de agregar un capítulo.");
      return;
    }

    // Validar el título
    const titulo = $tituloInput.val().trim();
    if (!titulo) {
      alert("El título no puede estar vacío.");
      return;
    }

    // Validar la página final
    const paginaFinalStr = $paginaFinalInput.val().trim();
    const paginaFinal = Number(paginaFinalStr);
    if (!Number.isInteger(paginaFinal) || paginaFinal < siguientePagina) {
      alert("La página de finalización debe ser un número válido mayor o igual a la página inicial (" + siguientePagina + ").");
      return;
    }

    const paginaInicio = siguientePagina;
    const numPaginas = paginaFinal - paginaInicio + 1;
    if (numPaginas > 200) {
      alert("No se puede agregar un número de folio que exceda los 200 folios.");
      return;
    }

    // Construir el título final con la etiqueta seleccionada
    const tituloCompleto = `${etiquetaSeleccionada}: ${titulo}`;

    // Enviar la solicitud AJAX para agregar el nuevo capítulo
    $.ajax({
      url: agregarCapituloURL,
      type: "POST",
      data: {
        caja: caja,
        carpeta: carpeta,
        titulo: tituloCompleto,
        paginaFinal: paginaFinal
      },
      dataType: "json"
    })
    .done((response) => {
      if (response.status === "success") {
        const nuevoCapitulo = response.capitulo;

        // Eliminar fila placeholder en caso de que exista
        $capitulosTableBody.find("tr").filter(function() {
          return $(this).text().includes("No hay capítulos registrados");
        }).remove();

        // Agregar la nueva fila a la tabla
        const nuevaFila = $(`
          <tr data-id="${nuevoCapitulo.id}" data-num-paginas="${nuevoCapitulo.num_paginas}">
            <td>
              <button type="button" class="btn btn-light btn-sm p-0 border-0 drag-handle" style="background: yellow; border: 1px solid red;">
                <i class="fas fa-arrows-alt-v" style="color: black; font-size: 1.5rem;"></i>
              </button>
            </td>
            <td contenteditable="true" class="editable">${nuevoCapitulo.titulo}</td>
            <td>${nuevoCapitulo.pagina_inicio}</td>
            <td>${nuevoCapitulo.pagina_final}</td>
            <td>
              <button class="btn btn-success btn-sm eliminar" style="padding: 0.2rem 0.4rem; font-size: 0.7rem;">Eliminar</button>
            </td>
          </tr>
        `);
        $capitulosTableBody.append(nuevaFila);

        // Actualizar la siguiente página y otros elementos de la UI
        siguientePagina = Number(nuevoCapitulo.pagina_final) + 1;
        $ultimaPagina.text(`Última página: ${siguientePagina}`);
        $paginaFinalInput.val(siguientePagina);
        $ultimaPagina1.val(nuevoCapitulo.pagina_final);
        $tituloInput.val("").focus();
        $("#charCount").text("0 / 394");

        // Desplazar la vista al final de la página
        $("html, body").animate({ scrollTop: $(document).height() }, 500);

        // Actualizar el <select> en la celda del último capítulo
        actualizarSelectFinal();
      } else {
        alert(response.message || "Error al agregar el capítulo.");
      }
    })
    .fail((xhr, status, error) => {
      console.error("Error en la solicitud AJAX:", error, status, xhr.responseText);
      alert(`Error: ${xhr.status} - ${xhr.statusText}\nDetalles: ${xhr.responseText}`);
    });
  });

  // Al cargar la página, si ya hay capítulos, actualizar el select en el último capítulo
  actualizarSelectFinal();
});

    
    


//5. Agregar un nuevo capítulo Tecla ENTER
    $("#titulo").keypress(function(event) {
        if (event.which === 13) { // 13 es el código de la tecla Enter
            event.preventDefault(); // Evita que se envíe el formulario
            agregarCapitulo(); // Llama a la función para agregar el capítulo
            $("#titulo").val(''); // Limpia el textarea
        }
    });

    

//6. Función para recalcular las páginas y actualizar los IDs después del reordenamiento
function actualizarPaginas() {
    let siguientePagina = 1;         // Página inicial para el primer capítulo
    let ultimaPaginaCalculada = 0;   // Última página calculada globalmente
    let nuevoId2 = 1;                // ID inicial para el primer capítulo

    // Itera sobre cada fila (capítulo) de la tabla
    $("#capitulosTable tbody tr").each(function() {
        const $fila = $(this);

        // Extraer el número de páginas desde el atributo data-num-paginas
        const numPaginas = parseInt($fila.attr("data-num-paginas"), 10);
        if (isNaN(numPaginas) || numPaginas < 1) {
            console.error(`Error: Número de páginas inválido en la fila ${$fila.index() + 1}`);
            return; // Salta la fila si el número es inválido
        }

        // Calcular la página de inicio y final para el capítulo actual
        const paginaInicio = siguientePagina;
        const paginaFinal = paginaInicio + numPaginas - 1;

        // Actualiza el input (si existe) que muestra la última página calculada
        $("#ultimaPagina1").val(`${paginaFinal}`);

        // Actualizar las celdas de la fila con los nuevos valores
        // Asumiendo que la columna 2 es "Página de inicio" y la columna 3 es "Página final"
        $fila.find("td:eq(2)").text(paginaInicio);
        $fila.find("td:eq(3)").text(paginaFinal);

        // Actualizar el atributo data-id y la celda visible (columna 0) con el nuevo ID
        $fila.attr("data-id", nuevoId2);
        $fila.find("td:eq(0)").text(nuevoId2);

        // Actualizar la siguiente página para el siguiente capítulo
        siguientePagina = paginaFinal + 1;
        nuevoId2++;

        // Mantener el seguimiento de la última página calculada
        ultimaPaginaCalculada = paginaFinal;
    });

    // Actualizar la última página global mediante una función auxiliar (defínela en tu script)
    actualizarUltimaPagina(ultimaPaginaCalculada);
}


//7. Función para actualizar la última página en la interfaz
/**
 * Actualiza la última página en la interfaz.
 * Calcula la siguiente página (ultimaPagina + 1), actualiza el texto y el valor de los inputs.
 * @param {number} ultimaPagina - La última página calculada.
 * @returns {number} La siguiente página calculada.
 */
function actualizarUltimaPagina(ultimaPagina) {
  // Calcular la siguiente página
  const nuevaSiguientePagina = ultimaPagina + 1;
  
  // Actualizar el texto que muestra la última página en la interfaz
  $("#ultimaPagina").text(`Última página: ${nuevaSiguientePagina}`);
  
  // Actualizar el valor del input "paginaFinal"
  $("#paginaFinal").val(nuevaSiguientePagina);
  
  // Si manejas otra variable global o input para la última página, actualízalo aquí.
  // Se removió la verificación de 'pagina_final' porque no está definida.
  
  return nuevaSiguientePagina;
}
// Fin del script 7

  

// 8. Reordenar las filas de la tabla utilizando jQuery UI sortable
$(document).ready(function() {
  $("#capitulosTable tbody").sortable({
    items: "tr",
    cursor: "move",
    placeholder: "highlight",
    cancel: "", // Permite que el botón sea arrastrable
    handle: ".drag-handle", // Usamos la clase del botón de arrastre
    update: function() {
      // Actualizar atributos y celdas sin modificar el botón de arrastre
      $("#capitulosTable tbody tr").each(function(index) {
        const $fila = $(this);
        const nuevoId = index + 1;
        // Actualiza el atributo data-id de la fila
        $fila.attr("data-id", nuevoId);
        const numPaginas = parseInt($fila.attr("data-num-paginas"), 10);
        const paginaInicio = (index === 0)
          ? 1
          : parseInt($fila.prev().find("td:eq(3)").text(), 10) + 1;
        const paginaFinal = paginaInicio + numPaginas - 1;
        $fila.find("td:eq(2)").text(paginaInicio);
        $fila.find("td:eq(3)").text(paginaFinal);
      });
      
      // Construir el nuevo orden para enviar vía AJAX
      const nuevoOrden = $("#capitulosTable tbody tr").map((index, element) => {
        const $fila = $(element);
        const nuevoId = index + 1;
        const titulo = $fila.find("td:eq(1)").text().trim();
        const inicio = parseInt($fila.find("td:eq(2)").text(), 10);
        const fin = parseInt($fila.find("td:eq(3)").text(), 10);
        const paginas = fin - inicio + 1;
  
        return { id: nuevoId, titulo, inicio, fin, paginas };
      }).get();
      
      // Obtener valores de caja y carpeta, convertir a JSON, enviar AJAX, etc.
      const config = $("#config");
      const caja = Number(config.data("caja"));
      const carpeta = Number(config.data("carpeta"));
      const jsonData = JSON.stringify({
        cambios: nuevoOrden,
        caja: caja,
        carpeta: carpeta
      });
      const actualizarOrdenURL = config.data("actualizar-orden");
  
      $.ajax({
        url: actualizarOrdenURL,
        method: "POST",
        data: { data: jsonData },
        dataType: "json",
        success: function(response) {
          console.log("Actualización exitosa:", response);
          // Llamar a la función para actualizar el select en la última fila
          actualizarSelectFinal();
        },
        error: function(xhr, status, error) {
          console.error("Error en la actualización:", error);
          alert("Error al actualizar: " + error);
          // Incluso en caso de error, podrías querer actualizar el select
          actualizarSelectFinal();
        }
      });
    }
  });
});// Fin del script 8




   //9. Función para actualizar la columna de arrastre sin sobrescribir el botón si ya existe  
   function actualizarColumnasMover() {
    $("#capitulosTable tbody tr").each(function() {
      const $fila = $(this);
      // Tomamos la primera columna de la fila
      const $firstCell = $fila.find("td:first");
      
      // Le asignamos la clase drag-column si no la tiene
      if (!$firstCell.hasClass("drag-column")) {
        $firstCell.addClass("drag-column");
      }
      
      // Verificamos si tiene el botón de arrastre; si no, lo inyectamos
      if (!$firstCell.find("button.drag-handle").length) {
        $firstCell.html(
          '<button type="button" class="btn btn-light btn-sm p-0 border-0 drag-handle">' +
            '<i class="fas fa-arrows-alt-v" style="color: black; font-size: 1.5rem;"></i>' +
          '</button>'
        );
      }
    });
  }
  
  


  //10. Código para eliminar un capítulo
  $(document).off("click", ".eliminar").on("click", ".eliminar", function() {
    const $fila = $(this).closest("tr");
    const idCapitulo = $fila.data("id");
  
    // Obtener 'caja', 'carpeta' y la URL del endpoint desde el contenedor de configuración
    const config = $("#config");
    const caja = Number(config.data("caja"));
    const carpeta = Number(config.data("carpeta"));
    const eliminarCapituloURL = config.data("eliminar-capitulo");
  
    if (confirm("¿Está seguro de que desea eliminar este capítulo?")) {
      $.ajax({
        url: eliminarCapituloURL,
        type: "POST",
        data: {
          id: idCapitulo,
          caja: caja,
          carpeta: carpeta
        },
        dataType: "json",
        success: function(response) {
          if (response.status === "success") {
            // Eliminar la fila del capítulo
            $fila.remove();
  
            // Si ya no hay capítulos en la tabla, insertar una fila placeholder
            if ($("#capitulosTable tbody tr").length === 0) {
              $("#capitulosTable tbody").append(
                `<tr>
                   <td colspan="5" class="text-center">No hay capítulos registrados. Página inicial: 1</td>
                 </tr>`
              );
            }
            
            // Recalcular las páginas, actualizar las columnas de arrastre y refrescar el select externo
            actualizarPaginas();
            actualizarColumnasMover();
            actualizarSelectFinal();
          } else {
            alert(response.message || "Error al eliminar el capítulo.");
          }
        },
        error: function(xhr, status, error) {
          console.error("Error en la solicitud AJAX:", error, status, xhr.responseText);
          alert("Error al eliminar el capítulo. Por favor, intenta nuevamente.");
        }
      });
    }
  });  //10. FINAL Código para eliminar un capítulo
  





//11. Estado global para el reconocimiento de voz
let grabando = false;
let recognition; // Objeto de reconocimiento de voz
function iniciarReconocimiento() {
  if (!('webkitSpeechRecognition' in window)) {
    alert("Lo siento, tu navegador no soporta esta función.");
    return;
  }
  recognition = new webkitSpeechRecognition();
  recognition.lang = 'es-CO'; // Configurar el idioma (Español Colombia)
  recognition.continuous = true; // Reconocimiento continuo
  recognition.interimResults = false; // No mostrar resultados intermedios
  recognition.onresult = function(event) {
    const textarea = document.getElementById('titulo');
    let nuevoTexto = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const resultado = event.results[i];
      if (resultado.isFinal) {
        let textoReconocido = resultado[0].transcript;
        textoReconocido = textoReconocido.replace(/\balirio\b/gi, "Alirio")
 textoReconocido = textoReconocido.replace(/\balirio\b/gi, "Alirio")
                                .replace(/\barles\b/gi, "Arles")
                                .replace(/\bargotti\b/gi, "Argoty")
                                .replace(/\bbarreiro\b/gi, "Barreiro")
                                .replace(/\bbastidas\b/gi, "Bastidas")
                                .replace(/\bbelalcázar\b/gi, "Belalcázar")
                                .replace(/\bbravo\b/gi, "Bravo")
                                .replace(/\bbrisueno\b/gi, "Risueño")
                                .replace(/\bburbano\b/gi, "Burbano")
                                .replace(/\bcansimansi\b/gi, "Cansimansi")
                                .replace(/\bcalpa\b/gi, "Calpa")
                                .replace(/\bcalvache\b/gi, "Calvache")
                                .replace(/\bcalvacci\b/gi, "Calvachy")
                                .replace(/\bcalvachi\b/gi, "Calvachy")
                                .replace(/\bcalvachí\b/gi, "Calvachy")
                                .replace(/\bcollés\b/gi, "Goyes")
                                .replace(/\bcanal\b/gi, "Canal")
                                .replace(/\bcoral\b/gi, "Coral")
                                .replace(/\bcorrea\b/gi, "Correa")
                                .replace(/\bcortés\b/gi, "Cortés")
                                .replace(/\bcadena\b/gi, "Cadena")
                                .replace(/\bfarinango\b/gi, "Farinango")
                                .replace(/\bflores\b/gi, "Flores")
                                .replace(/\bcoyez\b/gi, "Goyes")
                                .replace(/\bderecho\b/gi, "Derecho")
                                .replace(/\bdolores\b/gi, "Dolores")
                                .replace(/\bedilma\b/gi, "Edilma")
                                .replace(/\bespecialización\b/gi, "Especialización")
                                .replace(/\berazo\b/gi, "Erazo")
                                .replace(/\bgalvis\b/gi, "Galvis")
                                .replace(/\bgiraldo\b/gi, "Giraldo")
                                .replace(/\bgoiles\b/gi, "Goyes")
                                .replace(/\bgoyes\b/gi, "Goyes")
                                .replace(/\bgoyés\b/gi, "Goyes")
                                .replace(/\bgoyez\b/gi, "Goyes")
                                .replace(/\bgoyis\b/gi, "Goyes")
                                .replace(/\bgoiz\b/gi, "Goyes")
                                .replace(/\bguerra\b/gi, "Guerra")
                                .replace(/\bhoyos\b/gi, "Hoyos")
                                .replace(/\bjojoa\b/gi, "Jojoa")
                                .replace(/\blagos\b/gi, "Lagos")
                                .replace(/\bleyton\b/gi, "Leyton")
                                .replace(/\blegis\b/gi, "LEGIS")
                                .replace(/\blegarda\b/gi, "Legarda")
                                .replace(/\blibardo\b/gi, "Libardo")
                                .replace(/\bmayama\b/gi, "Mayama")
                                .replace(/\bmadroñero\b/gi, "Madroñero")
                                .replace(/\bmarco\b/gi, "Marco")
                                .replace(/\bmaterón\b/gi, "Materón")
                                .replace(/\bmiriam\b/gi, "Myriam")
                                .replace(/\bmorasurco\b/gi, "Morasurco")
                                .replace(/\bmunera\b/gi, "Munera")
                                .replace(/\bmaigual\b/gi, "Maigual")
                                .replace(/\bmoncayo\b/gi, "Moncayo")
                                .replace(/\bnariño\b/gi, "Nariño")
                                .replace(/\bnavia\b/gi, "Navia")
                                .replace(/\bocaña\b/gi, "Ocaña")
                                .replace(/\boliva\b/gi, "Oliva")
                                .replace(/\bosejo\b/gi, "Osejo")
                                .replace(/\bocara\b/gi, "OCARA")
                                .replace(/\bpalacios\b/gi, "Palacios")
                                .replace(/\bparedes\b/gi, "Paredes")
                                .replace(/\bpasos\b/gi, "Pasos")
                                .replace(/\bpinilla\b/gi, "Pinilla")
                                .replace(/\bPara\b/gi, "para")
                                .replace(/\bramos\b/gi, "Ramos")
                                .replace(/\breina\b/gi, "Reina")
                                .replace(/\brengifo\b/gi, "Rengifo")
                                .replace(/\brisueño\b/gi, "Risueño")
                                .replace(/\brevelo\b/gi, "Revelo")
                                .replace(/\bregalado\b/gi, "Regalado")
                                .replace(/\briascos\b/gi, "Riascos")
                                .replace(/\brosa\b/gi, "Rosa")
                                .replace(/\brojas\b/gi, "Rojas")
                                .replace(/\bsalas\b/gi, "Salas")
                                .replace(/\bsañudo\b/gi, "Sañudo")
                                .replace(/\bsarama\b/gi, "Zarama")
                                .replace(/\bsolarte\b/gi, "Solarte")
                                .replace(/\bsotelo\b/gi, "Sotelo")
                                .replace(/\btajumbina\b/gi, "Tajumbina")
                                .replace(/\btenganán\b/gi, "Tenganán")
                                .replace(/\btoro\b/gi, "Toro")
                                .replace(/\btutistar\b/gi, "Tutistar")
                                .replace(/\buniversidad\b/gi, "Universidad")
                                .replace(/\burresta\b/gi, "Urresta")
                                .replace(/\bureña\b/gi, "Ureña")
                                .replace(/\burbano\b/gi, "Urbano")
                                .replace(/\bvaca\b/gi, "Vaca")
                                .replace(/\bvela\b/gi, "Vela")
                                .replace(/\bvillota\b/gi, "Villota")
                                .replace(/\bvinueza\b/gi, "Vinueza")
                                .replace(/\bviteri\b/gi, "Viteri")
                                .replace(/\bzarama\b/gi, "Zarama");
        nuevoTexto += (nuevoTexto ? " " : "") + textoReconocido;
      }
    }
    textarea.value += nuevoTexto.trim() + " ";
    textarea.focus();
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
  };
  recognition.onend = function() {
    if (grabando) {
      recognition.start();
    }
  };
  recognition.start();
  grabando = true;
  document.getElementById('grabarBoton').classList.add('grabando'); // Cambia el estilo (por ejemplo, color verde)
}
function detenerReconocimiento() {
  if (recognition) {
    recognition.stop();
  }
  grabando = false;
  document.getElementById('grabarBoton').classList.remove('grabando'); // Cambia el estilo (por ejemplo, color rojo)
  const textarea = document.getElementById('titulo');
  textarea.focus();
  textarea.setSelectionRange(textarea.value.length, textarea.value.length);
}
document.getElementById('grabarBoton').addEventListener('click', function() {
  if (!grabando) {
    iniciarReconocimiento();
  } else {
    detenerReconocimiento();
  }
});
document.addEventListener('keydown', function(event) {
  if (event.key === 'F9' && !grabando) {
    iniciarReconocimiento();
  }
});
document.addEventListener('keyup', function(event) {
  if (event.key === 'F9' && grabando) {
    detenerReconocimiento();
  }
});// FINAL  SCRIPT 11. Estado global para el reconocimiento de voz



//12. Cuando se presiona la tecla ENTER en un elemento editable, se guarda el nuevo título con la tecla ENTER
$(document).on("keydown", ".editable", function(event) {
  if (event.key === "Enter") {
      event.preventDefault(); // Evita salto de línea
      const $this = $(this);
      const nuevoTitulo = $this.text().trim();
      if (!nuevoTitulo) {
          alert("El título no puede estar vacío.");
          $this.text("Título"); // Restaurar texto predeterminado
          return;
      }

      // Obtener datos necesarios: id, caja y carpeta
      const $fila = $this.closest("tr");
      const id2 = $fila.data("id");
      const config = $("#config");
      const caja = Number(config.data("caja"));
      const carpeta = Number(config.data("carpeta"));
      const actualizarTituloURL = config.data("actualizar-titulo");

      // Realizar la solicitud AJAX para actualizar el título
      $.ajax({
          url: actualizarTituloURL,
          type: "POST",
          data: {
              id: id2,
              caja: caja,
              carpeta: carpeta,
              titulo: nuevoTitulo
          },
          dataType: "json",
          success: function(response) {
              if (response.status === "success") {
                  console.log("Título actualizado correctamente.");
                  // Enfocar en el textarea 'titulo' después de guardar
                  $("#titulo").focus();
              } else {
                  alert(response.message || "Error al actualizar el título.");
              }
          },
          error: function(xhr, status, error) {
              console.error("Error en la solicitud AJAX:", error, status, xhr.responseText);
              alert("Error al actualizar el título.");
          }
      });
  }
});


  
  

//13. INICIA la página con el número de páginas correctos de cada capítulo
function actualizarSelectFinal() {
  const $lastRow = $("#capitulosTable tbody tr:last");
  if (!$lastRow.length) {
    console.warn("No se encontró ningún capítulo en la tabla.");
    return;
  }

  // Extraer la página inicial y la página final actual del capítulo
  const startPage = parseInt($lastRow.find("td:eq(2)").text().trim(), 10);
  const currentFinalPage = parseInt($lastRow.find("td:eq(3)").text().trim(), 10);
  if (isNaN(startPage)) {
    console.warn("La página inicial no es un número válido.");
    return;
  }

  // Regenerar las opciones del select desde startPage hasta 200
  let optionsHTML = "";
  for (let i = startPage; i <= 200; i++) {
    optionsHTML += `<option value="${i}" ${i === currentFinalPage ? "selected" : ""}>${i}</option>`;
  }
  $("#finalPageSelect").html(optionsHTML);

  $("#finalPageSelect").off("change").on("change", function () {
    const newFinalPage = parseInt($(this).val(), 10);
    console.log("Nuevo valor seleccionado:", newFinalPage);

    if (newFinalPage < startPage) {
      alert(`La página final no puede ser menor que la página inicial (${startPage}).`);
      $(this).val(currentFinalPage);
      return;
    }

    // Si se selecciona un valor diferente al actual, se actualiza la celda en la tabla y se sincroniza vía AJAX
    if (newFinalPage !== currentFinalPage) {
      // Actualizar el contenido de la celda en la tabla
      $lastRow.find("td:eq(3)").text(newFinalPage);

      // Actualizar otros elementos de la UI
      $("#ultimaPagina").text(`Última página: ${newFinalPage + 1}`);
      $("#paginaFinal").val(newFinalPage + 1);

      // Actualizamos el atributo "data-num-paginas" en la fila para que refleje el nuevo número de folios
      const newNumPaginas = newFinalPage - startPage + 1;
      $lastRow.attr("data-num-paginas", newNumPaginas);

      // Obtener datos de configuración para la actualización en el servidor
      const config = $("#config");
      const caja = Number(config.data("caja"));
      const carpeta = Number(config.data("carpeta"));
      const chapterId = $lastRow.data("id");
      const actualizarFinalURL = config.data("actualizar-final");

      // Enviar la solicitud AJAX para actualizar la página final en la base de datos
      $.ajax({
        url: actualizarFinalURL,
        type: "POST",
        data: {
          id: chapterId,
          caja: caja,
          carpeta: carpeta,
          paginaFinal: newFinalPage
        },
        dataType: "json",
        success: function(response) {
          if (response.status === "success") {
            console.log(`Página final actualizada correctamente a: ${newFinalPage}`);
          } else {
            alert(response.message || "Error al actualizar la página final.");
            $("#finalPageSelect").val(currentFinalPage);
            $lastRow.find("td:eq(3)").text(currentFinalPage);
          }
        },
        error: function(xhr, status, error) {
          console.error("Error en la solicitud AJAX:", error);
          alert("Error al actualizar la página final.");
          $("#finalPageSelect").val(currentFinalPage);
          $lastRow.find("td:eq(3)").text(currentFinalPage);
        }
      });
    }
  });
}
// Fin del script: actualizarSelectFinal()
