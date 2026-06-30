const API_URL = "http://localhost:8000";

let authToken = null;

// Cargar usuarios al iniciar la página
document.addEventListener("DOMContentLoaded", () => {
    loadUsers();
});

async function authenticate() {
    try {
        const response = await fetch(`${API_URL}/usuarios/autenticar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: "supervisor@test.com", password: "Test1234" })
        });
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
        } else {
            console.error("Error autenticando", await response.text());
        }
    } catch (error) {
        console.error("Error de red en autenticación", error);
    }
}

async function loadUsers() {
    const tbody = document.getElementById("users-table-body");
    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Cargando datos desde FastAPI...</td></tr>';
    
    if (!authToken) {
        await authenticate();
    }
    
    try {
        const response = await fetch(`${API_URL}/usuarios/`, {
            headers: {
                "Authorization": `Bearer ${authToken}`
            }
        });
        if (!response.ok) throw new Error(`Error en la red: ${response.status}`);
        
        const users = await response.json();
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">No hay usuarios registrados.</td></tr>';
            return;
        }

        tbody.innerHTML = "";
        users.forEach(user => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><code>${user.id}</code></td>
                <td>${user.nombre}</td>
                <td>${user.email}</td>
                <td><span class="badge badge-success">${user.rol}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error("Error cargando usuarios:", error);
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Error conectando con la API (Revisa que FastAPI esté corriendo)</td></tr>';
    }
}

async function createUser() {
    const name = document.getElementById("u-name").value;
    const email = document.getElementById("u-email").value;

    if(!name || !email) {
        alert("Completar todos los campos");
        return;
    }

    const payload = {
        nombre: name,
        email: email,
        rol: "solicitante",
        password: "Test1234"
    };

    try {
        const response = await fetch(`${API_URL}/usuarios/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            // Cerrar modal de bootstrap
            $('#userModal').modal('hide');
            // Limpiar form
            document.getElementById("form-user").reset();
            // Recargar tabla
            loadUsers();
            alert("Usuario creado con éxito en MongoDB via FastAPI");
        } else {
            alert("Error al crear usuario");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Error de red al crear usuario");
    }
}
