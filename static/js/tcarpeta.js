// Cargar subseries al cambiar la serie
$(document).ready(function () {
  $('#serie').change(function () {
    var serieNombre = $(this).find("option:selected").text();
    $('#subserie').empty();
    $('#subserie').append('<option value="" selected>Seleccione una Subserie</option>');
  
    if (serieNombre) {
      $.ajax({
        url: getSubseriesURL,
        type: 'POST',
        data: { serie_id: serieNombre },
        success: function (response) {
          var subseries = response; // Suponiendo que ya viene en JSON
          if (Array.isArray(subseries)) {
            subseries.forEach(function (subserie) {
              $('#subserie').append(
                '<option value="' + subserie.nombre + '">' + subserie.nombre + '</option>'
              );
            });
          } else if (subseries.error) {
            alert(subseries.error);
          }
        },
        error: function () {
          alert('Error al cargar las subseries. Inténtalo de nuevo más tarde.');
        }
      });
    }
  });
});

  
  // Limitar caracteres en el textarea
  document.getElementById('tituloCarpeta').addEventListener('input', function() {
    if (this.value.length > 56) {
      this.value = this.value.substring(0, 56);
    }
  });
  
  // DOMContentLoaded: Validación de fechas y reconocimiento de voz
  document.addEventListener('DOMContentLoaded', function () {
    // Validación de fechas
    const fechaInicialInput = document.getElementById('fechaInicial');
    const fechaFinalInput = document.getElementById('fechaFinal');
  
    function validarFechaActual(input) {
      const fechaActual = new Date().toISOString().split('T')[0];
      if (input.value > fechaActual) {
        alert('La fecha ingresada no puede ser mayor a la fecha actual.');
        input.value = '';
        input.focus();
      }
    }
  
    function validarRangoFechas() {
      if (fechaInicialInput.value && fechaFinalInput.value) {
        if (fechaInicialInput.value > fechaFinalInput.value) {
          alert('La fecha final no puede ser menor que la fecha inicial.');
          fechaFinalInput.value = '';
          fechaFinalInput.focus();
        }
      }
    }
  
    fechaInicialInput.addEventListener('change', function () {
      validarFechaActual(fechaInicialInput);
      validarRangoFechas();
    });
  
    fechaFinalInput.addEventListener('change', function () {
      validarFechaActual(fechaFinalInput);
      validarRangoFechas();
    });
  
    // Poner el foco en el textarea
    document.getElementById('tituloCarpeta').focus();
  
    // Reconocimiento de voz
    let recognition;
    let grabando = false;
  
    function iniciarReconocimiento() {
      if (!('webkitSpeechRecognition' in window)) {
        alert("Lo siento, tu navegador no soporta el reconocimiento de voz.");
        return;
      }
      recognition = new webkitSpeechRecognition();
      recognition.lang = 'es-ES';
      recognition.interimResults = false;
  
      recognition.onresult = function(event) {
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const resultado = event.results[i];
          if (resultado.isFinal) {
            let texto = resultado[0].transcript;
            texto = texto.replace(/\bcolombia\b/g, "Colombia");
            const textarea = document.getElementById('tituloCarpeta');
            if (textarea.value.length + texto.length > 56) {
              const espacioLibre = 56 - textarea.value.length;
              textarea.value += texto.substring(0, espacioLibre) + " ";
            } else {
              textarea.value += texto + " ";
            }
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
          }
        }
      };
  
      recognition.onerror = function(event) {
        console.error("Error en el reconocimiento:", event.error);
      };
  
      recognition.onend = function() {
        if (grabando) {
          recognition.start();
        }
      };
  
      recognition.start();
      grabando = true;
      document.getElementById('grabarBoton').classList.add('grabando');
    }
  
    function detenerReconocimiento() {
      if (recognition) {
        recognition.stop();
      }
      grabando = false;
      document.getElementById('grabarBoton').classList.remove('grabando');
      const textarea = document.getElementById('tituloCarpeta');
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
  
    // Uso de la tecla F9 para iniciar/detener reconocimiento
    document.addEventListener('keydown', function(event) {
      if (event.key === 'F9' && !grabando) {
        event.preventDefault();
        iniciarReconocimiento();
      }
    });
  
    document.addEventListener('keyup', function(event) {
      if (event.key === 'F9' && grabando) {
        event.preventDefault();
        detenerReconocimiento();
      }
    });
  });
  