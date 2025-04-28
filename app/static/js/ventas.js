document.addEventListener('DOMContentLoaded', function() {
    // Estado de la aplicación
    const appState = {
        productos: [],
        busquedaResultados: []
    };
    
    // Referencias a elementos DOM
    const elements = {
        searchInput: document.getElementById('producto-search'),
        searchResults: document.getElementById('resultados-busqueda'),
        productosTable: document.getElementById('productos-venta').querySelector('tbody'),
        noProductos: document.getElementById('no-productos'),
        totalItems: document.getElementById('total-items'),
        summarySubtotal: document.getElementById('summary-subtotal'),
        summaryIva: document.getElementById('summary-iva'),
        summaryTotal: document.getElementById('summary-total'),
        productosJson: document.getElementById('productos-json'),
        formVenta: document.getElementById('form-venta'),
        metodoPago: document.getElementById('metodo_pago'),
        clienteInput: document.getElementById('cliente_id'),
        finalizarBtn: document.getElementById('finalizar-venta')
    };
    
    // Inicializar
    updateVisibility();
    
    // Event listeners para productos disponibles
    document.querySelectorAll('.agregar-producto').forEach(btn => {
        btn.addEventListener('click', function() {
            const cantidadInput = this.closest('.card-body').querySelector('.cantidad-input');
            const cantidad = parseInt(cantidadInput.value) || 1;
            
            const producto = {
                id: this.dataset.id,
                nombre: this.dataset.nombre,
                precio: parseFloat(this.dataset.precio),
                stock: parseInt(this.dataset.cantidad),
                cantidad: cantidad,
                subtotal: parseFloat(this.dataset.precio) * cantidad
            };
            
            agregarProducto(producto);
        });
    });
    
    // Controles de cantidad en productos disponibles
    document.querySelectorAll('.btn-increase').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.closest('.input-group').querySelector('.cantidad-input');
            const max = parseInt(input.max);
            if (parseInt(input.value) < max) {
                input.value = parseInt(input.value) + 1;
            }
        });
    });
    
    document.querySelectorAll('.btn-decrease').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.closest('.input-group').querySelector('.cantidad-input');
            if (parseInt(input.value) > 1) {
                input.value = parseInt(input.value) - 1;
            }
        });
    });
    
    // Búsqueda de productos
    elements.searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length >= 2) {
            buscarProductos(query);
        } else {
            clearSearchResults();
        }
    });
    
    // Finalizar venta - Versión corregida
    elements.finalizarBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        
        // Resetear errores
        elements.metodoPago.classList.remove('is-invalid');
        
        // Validar método de pago
        if (!elements.metodoPago.value) {
            showAlert('Por favor seleccione un método de pago', 'danger');
            elements.metodoPago.classList.add('is-invalid');
            elements.metodoPago.focus();
            return;
        }
        
        // Validar productos
        if (appState.productos.length === 0) {
            showAlert('Debes agregar al menos un producto a la venta', 'danger');
            return;
        }
        
        // Mostrar loader o feedback visual
        elements.finalizarBtn.disabled = true;
        elements.finalizarBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        
        try {
            // Preparar datos JSON
            const productosData = appState.productos.map(p => ({
                id: p.id,
                cantidad: p.cantidad,
                precio: p.precio,
                subtotal: p.subtotal
            }));
            
            // Calcular totales
            const subtotal = appState.productos.reduce((sum, p) => sum + p.subtotal, 0);
            const iva = subtotal * 0.16;
            const total = subtotal + iva;
            
            // Crear FormData para enviar
            const formData = new FormData();
            formData.append('cliente_id', elements.clienteInput.value);
            formData.append('metodo_pago', elements.metodoPago.value);
            formData.append('productos_json', JSON.stringify(productosData));
            formData.append('subtotal', subtotal.toFixed(2));
            formData.append('iva', iva.toFixed(2));
            formData.append('total', total.toFixed(2));
            formData.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);
            
            // Enviar datos via fetch para mejor manejo de la respuesta
            const response = await fetch(elements.formVenta.action, {
                method: 'POST',
                body: formData
            });
            
            if (response.redirected) {
                // Si hay redirección, seguirla
                window.location.href = response.url;
            } else {
                const data = await response.json();
                if (data.success) {
                    window.location.href = data.redirect || '/registro-ventas';
                } else {
                    showAlert(data.message || 'Error al registrar la venta', 'danger');
                }
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('Error de conexión. Intente nuevamente.', 'danger');
        } finally {
            elements.finalizarBtn.disabled = false;
            elements.finalizarBtn.innerHTML = '<i class="fas fa-check me-2"></i> Finalizar Venta';
        }
    });
    
    // Funciones auxiliares
    function showAlert(message, type) {
        // Eliminar alertas previas
        document.querySelectorAll('.alert-dismissible').forEach(alert => alert.remove());
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
    }
    
    function buscarProductos(query) {
        fetch(`/api/productos/buscar?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                appState.busquedaResultados = data;
                renderSearchResults();
            })
            .catch(error => console.error('Error:', error));
    }
    
    function renderSearchResults() {
        elements.searchResults.innerHTML = '';
    
        if (appState.busquedaResultados.length === 0) {
            elements.searchResults.innerHTML = '<div class="p-3 text-center">No se encontraron productos</div>';
            elements.searchResults.classList.remove('d-none');
            return;
        }
    
        const resultsList = document.createElement('div');
        resultsList.className = 'list-group';
    
        appState.busquedaResultados.forEach(producto => {
            const item = document.createElement('div');
            item.className = 'list-group-item';
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${producto.nombre}</strong>
                        <div class="text-muted">$${producto.precio.toFixed(2)}</div>
                    </div>
                    <div class="d-flex align-items-center">
                        <span class="badge ${producto.cantidad > 5 ? 'bg-success' : 'bg-warning'} me-2">
                            Stock: ${producto.cantidad}
                        </span>
                        <button type="button" class="btn btn-sm btn-primary agregar-desde-busqueda"
                                data-id="${producto.id}"
                                data-nombre="${producto.nombre}"
                                data-precio="${producto.precio}"
                                data-cantidad="${producto.cantidad}">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                </div>
            `;
            resultsList.appendChild(item);
        });
    
        elements.searchResults.appendChild(resultsList);
        elements.searchResults.classList.remove('d-none');
    
        document.querySelectorAll('.agregar-desde-busqueda').forEach(btn => {
            btn.addEventListener('click', function() {
                const producto = {
                    id: this.dataset.id,
                    nombre: this.dataset.nombre,
                    precio: parseFloat(this.dataset.precio),
                    stock: parseInt(this.dataset.cantidad),
                    cantidad: 1,
                    subtotal: parseFloat(this.dataset.precio)
                };
    
                agregarProducto(producto);
                clearSearchResults();
                elements.searchInput.value = '';
            });
        });
    }
    
    function agregarProducto(producto) {
        const existingIndex = appState.productos.findIndex(p => p.id === producto.id);
        
        if (existingIndex >= 0) {
            const nuevaCantidad = appState.productos[existingIndex].cantidad + producto.cantidad;
            if (nuevaCantidad <= producto.stock) {
                appState.productos[existingIndex].cantidad = nuevaCantidad;
                appState.productos[existingIndex].subtotal = appState.productos[existingIndex].precio * nuevaCantidad;
            } else {
                showAlert('No hay suficiente stock disponible', 'warning');
                return;
            }
        } else {
            appState.productos.push(producto);
        }
        
        renderProductosVenta();
        updateTotales();
    }
    
    function renderProductosVenta() {
        elements.productosTable.innerHTML = '';
        
        appState.productos.forEach((producto, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${producto.nombre}</td>
                <td>$${producto.precio.toFixed(2)}</td>
                <td>${producto.stock}</td>
                <td>
                    <div class="input-group input-group-sm">
                        <button type="button" class="btn btn-outline-secondary btn-decrease">-</button>
                        <input type="number" class="form-control text-center producto-cantidad" 
                               value="${producto.cantidad}" min="1" max="${producto.stock}">
                        <button type="button" class="btn btn-outline-secondary btn-increase">+</button>
                    </div>
                </td>
                <td>$${producto.subtotal.toFixed(2)}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger btn-remove">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            
            elements.productosTable.appendChild(row);
            
            // Event listeners para controles
            const btnDecrease = row.querySelector('.btn-decrease');
            const btnIncrease = row.querySelector('.btn-increase');
            const btnRemove = row.querySelector('.btn-remove');
            const inputCantidad = row.querySelector('.producto-cantidad');
            
            btnDecrease.addEventListener('click', () => {
                if (producto.cantidad > 1) {
                    producto.cantidad--;
                    producto.subtotal = producto.precio * producto.cantidad;
                    renderProductosVenta();
                    updateTotales();
                }
            });
            
            btnIncrease.addEventListener('click', () => {
                if (producto.cantidad < producto.stock) {
                    producto.cantidad++;
                    producto.subtotal = producto.precio * producto.cantidad;
                    renderProductosVenta();
                    updateTotales();
                } else {
                    showAlert('No hay más stock disponible', 'warning');
                }
            });
            
            btnRemove.addEventListener('click', () => {
                appState.productos.splice(index, 1);
                renderProductosVenta();
                updateTotales();
                updateVisibility();
            });
            
            inputCantidad.addEventListener('change', (e) => {
                const newValue = parseInt(e.target.value);
                if (isNaN(newValue)) {
                    e.target.value = producto.cantidad;
                    return;
                }
                
                if (newValue < 1) {
                    e.target.value = 1;
                    producto.cantidad = 1;
                } else if (newValue > producto.stock) {
                    e.target.value = producto.stock;
                    producto.cantidad = producto.stock;
                    showAlert('Cantidad ajustada al máximo stock disponible', 'info');
                } else {
                    producto.cantidad = newValue;
                }
                
                producto.subtotal = producto.precio * producto.cantidad;
                updateTotales();
            });
        });
        
        updateVisibility();
    }
    
    function updateTotales() {
        const subtotal = appState.productos.reduce((sum, p) => sum + p.subtotal, 0);
        const iva = subtotal * 0.16;
        const total = subtotal + iva;
        
        elements.summarySubtotal.textContent = `$${subtotal.toFixed(2)}`;
        elements.summaryIva.textContent = `$${iva.toFixed(2)}`;
        elements.summaryTotal.textContent = `$${total.toFixed(2)}`;
        
        const totalItems = appState.productos.reduce((sum, p) => sum + p.cantidad, 0);
        elements.totalItems.textContent = `${totalItems} items`;
    }
    
    function updateVisibility() {
        if (appState.productos.length === 0) {
            elements.noProductos.classList.remove('d-none');
            elements.productosTable.closest('.table-responsive').classList.add('d-none');
        } else {
            elements.noProductos.classList.add('d-none');
            elements.productosTable.closest('.table-responsive').classList.remove('d-none');
        }
    }
    
    function clearSearchResults() {
        elements.searchResults.innerHTML = '';
        elements.searchResults.classList.add('d-none');
    }
    
    // Cerrar resultados al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (!elements.searchInput.contains(e.target) && !elements.searchResults.contains(e.target)) {
            clearSearchResults();
        }
    });
});