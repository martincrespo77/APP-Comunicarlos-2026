const API_URL = "http://localhost:8000";

// Cargar usuarios al iniciar la página
document.addEventListener("DOMContentLoaded", () => {
    loadUsers();
});

async function loadUsers() {
    const tbody = document.getElementById("users-table-body");
    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Cargando datos desde FastAPI...</td></tr>';
    
    try {
        const response = await fetch(`${API_URL}/users/`);
        if (!response.ok) throw new Error("Error en la red");
        
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
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td><span class="badge badge-success">${user.role}</span></td>
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
        name: name,
        email: email,
        role: "user"
    };

    try {
        const response = await fetch(`${API_URL}/users/`, {
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
