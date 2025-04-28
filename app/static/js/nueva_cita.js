document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('nuevaCitaForm');
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    
    // Función para mostrar estado de carga
    function updateLoading(message) {
        const loadingText = document.querySelector('#loadingModal .modal-body h5');
        if (loadingText) loadingText.textContent = message;
    }

    // Función para mostrar errores
    function showError(message) {
        Swal.fire({
            title: 'Error',
            text: message,
            icon: 'error',
            confirmButtonText: 'Entendido'
        });
    }

    // Cargar datos iniciales
    async function loadInitialData() {
        try {
            // Realizar todas las peticiones en paralelo
            const endpoints = [
                '/api/barberos',
                '/api/servicios',
                '/api/clientes'
            ];
            
            const responses = await Promise.all(
                endpoints.map(url => fetch(url).then(res => {
                    if (!res.ok) throw new Error(`Error ${res.status} al cargar ${url}`);
                    return res.json();
                }))
            );
            
            const [barberos, servicios, clientes] = responses;
            
            // Llenar select de barberos
            const barberoSelect = document.getElementById('barbero');
            barberoSelect.innerHTML = '<option value="">Seleccione un barbero</option>';
            barberos.forEach(barbero => {
                const option = new Option(
                    `${barbero.nombre || barbero.username} ${barbero.apellido || ''}`.trim(),
                    barbero.id
                );
                barberoSelect.add(option);
            });
            
            // Llenar select de servicios
            const servicioSelect = document.getElementById('servicio');
            servicioSelect.innerHTML = '<option value="">Seleccione un servicio</option>';
            servicios.forEach(servicio => {
                const option = new Option(servicio.nombre, servicio.id);
                servicioSelect.add(option);
            });
            
            // Configurar combobox de clientes
            const clienteCombobox = $('#clienteCombobox');
            clienteCombobox.empty();
            clienteCombobox.append('<option value=""></option>'); // Opción vacía
            
            // Agregar clientes existentes
            clientes.forEach(cliente => {
                clienteCombobox.append(
                    $('<option></option>').val(cliente.id).text(cliente.username)
                );
            });
            
            // Agregar opción de cliente general
            clienteCombobox.append(
                $('<option></option>').val(0).text('Cliente general')
            );
            
            // Configurar Select2
            clienteCombobox.select2({
                placeholder: "Buscar cliente o escribir nuevo",
                allowClear: true,
                tags: true,
                width: '100%',
                createTag: function(params) {
                    return {
                        id: params.term,
                        text: params.term + " (nuevo)",
                        isNew: true
                    };
                }
            });
            
        } catch (error) {
            console.error('Error cargando datos:', error);
            showError('Error al cargar los datos iniciales. Por favor recarga la página.');
            
            // Cargar servicios predeterminados si falla la API
            const servicioSelect = document.getElementById('servicio');
            servicioSelect.innerHTML = '<option value="">Seleccione un servicio</option>';
            const serviciosDefault = [
                {id: 1, nombre: 'Corte completo'},
                {id: 2, nombre: 'Corte barba'},
                {id: 3, nombre: 'Corte ceja'}
            ];
            serviciosDefault.forEach(servicio => {
                const option = new Option(servicio.nombre, servicio.id);
                servicioSelect.add(option);
            });
        }
    }

    // Manejar envío del formulario
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Validación básica
        const fecha = document.getElementById('fecha').value;
        const hora = document.getElementById('hora').value;
        const barberoSelect = document.getElementById('barbero');
        const servicioSelect = document.getElementById('servicio');
        const clienteCombobox = $('#clienteCombobox');
        
        if (!fecha || !hora || !barberoSelect.value || !servicioSelect.value || !clienteCombobox.val()) {
            showError('Por favor complete todos los campos requeridos');
            return;
        }

        updateLoading('Registrando cita...');
        loadingModal.show();

        try {
            const selectedClient = clienteCombobox.select2('data')[0];
            const isNewClient = selectedClient && selectedClient.isNew;

            const formData = {
                cliente: isNewClient ? selectedClient.text.replace(' (nuevo)', '') : clienteCombobox.val(),
                barbero_id: barberoSelect.value,
                servicio_id: servicioSelect.value,
                fecha_hora: `${fecha} ${hora}:00`,
                is_new_client: isNewClient,
                telefono: isNewClient ? document.getElementById('clientPhone').value : null,
                notas: document.getElementById('notas').value || ''
            };

            const response = await fetch('/admin/cita/registrar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            loadingModal.hide();

            if (data.success) {
                let successMessage = data.message;
                if (data.new_client_created) {
                    successMessage += '\nSe ha creado un nuevo cliente con los datos proporcionados.';
                }
                
                await Swal.fire({
                    title: '¡Éxito!',
                    text: successMessage,
                    icon: 'success'
                });
                window.location.href = '/admin/citas';
            } else {
                showError(data.message || 'Error desconocido al registrar la cita');
            }
        } catch (error) {
            loadingModal.hide();
            console.error('Error:', error);
            showError('Error de conexión al procesar la solicitud');
        }
    });

    // Iniciar carga de datos
    loadInitialData();
});