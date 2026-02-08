let pyodide;

// 1. Cargar el motor al iniciar
async function cargarMotor() {
    const boton = document.getElementById("boton-ejecutar");
    const output = document.getElementById("consola-output");
    
    if (boton) {
        boton.disabled = true;
        boton.style.opacity = "0.5";
        const textoBoton = boton.querySelector("span:last-child");
        if (textoBoton) textoBoton.innerText = "CARGANDO MAGIA... ✨";
    }

    try {
        pyodide = await loadPyodide();
        console.log("Python listo ✅");
        
        if (boton) {
            boton.disabled = false;
            boton.style.opacity = "1";
            const textoBoton = boton.querySelector("span:last-child");
            if (textoBoton) textoBoton.innerText = "¡EJECUTAR CÓDIGO!";
        }
        if (output) output.innerText = "¡Listo para empezar! Escribe tu código arriba.";
    } catch (err) {
        console.error("Error al cargar Pyodide:", err);
    }
}

// 2. Lógica de Ejecución y Validación
async function ejecutarPython() {
    const codigoInput = document.getElementById("codigo-input").value;
    const output = document.getElementById("consola-output");
    const burbuja = document.getElementById("lumi-burbuja");
    
    // Elementos de los objetivos (Checks)
    const check1 = document.getElementById("check-1");
    const check2 = document.getElementById("check-2");
    const check3 = document.getElementById("check-3");
    
    // Meta dinámica traída desde Django
    const metaEsperada = document.getElementById("input-meta") ? document.getElementById("input-meta").value.trim() : "";

    output.innerText = "Ejecutando... ⏳";
    if (burbuja) burbuja.innerText = "¡A ver, a ver! Estoy revisando tu magia... 🤔";

    try {
        // Redirigir la salida de Python para capturarla
        await pyodide.runPython(`
import sys
import io
sys.stdout = io.StringIO()
        `);

        // Ejecutar el código del niño
        await pyodide.runPython(codigoInput);
        
        // Obtener el resultado
        let resultado = pyodide.runPython("sys.stdout.getvalue()").trim();
        output.innerText = resultado || "El código corrió, pero no imprimió nada.";

        // --- VALIDACIÓN DE OBJETIVOS ---

        // Objetivo 3: ¡Hizo clic en ejecutar! (Siempre se cumple si llega aquí)
        marcarCheck(check3);

        // Objetivo 1: Validar si usó la función clave (ej: print)
        if (codigoInput.toLowerCase().includes("print")) {
            marcarCheck(check1);
        }

        // Objetivo 2: Validar si el resultado es igual a la meta de la lección
        if (resultado === metaEsperada) {
            marcarCheck(check2);
            
            // ¡EFECTO DE VICTORIA!
            if (typeof confetti === 'function') {
                confetti({
                    particleCount: 150,
                    spread: 70,
                    origin: { y: 0.6 },
                    colors: ['#ee2b6c', '#13ec80', '#D0EBFF']
                });
            }
            if (burbuja) burbuja.innerText = "¡GUAU! ¡Lo hiciste genial! Eres un mago de verdad. 🐰✨";
        } else {
            if (burbuja) burbuja.innerText = "¡Casi! Revisa que tu mensaje sea exactamente igual al del objetivo. 😊";
        }

    } catch (err) {
        output.innerText = "❌ Error en tu código:\n" + err;
        if (burbuja) burbuja.innerText = "¡Oh no! Hubo un pequeño error. ¡No te rindas! 🧐";
    }
}

// Función auxiliar para poner los checks en verde
function marcarCheck(elemento) {
    if (elemento) {
        elemento.innerText = "check_circle";
        elemento.classList.remove("text-slate-300");
        elemento.classList.add("text-green-500", "font-bold");
    }
}

// Inicializar al cargar la página
window.addEventListener('load', cargarMotor);