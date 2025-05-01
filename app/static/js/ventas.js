// Estado global de la aplicación
window.appState = {
    productos: [],
    busquedaResultados: [],
    descuento: 0
};

// Funciones globales
window.updateCantidad = function(productoId, delta) {
    const producto = window.appState.productos.find(p => p.id === productoId);
    if (!producto) return;

    const nuevaCantidad = producto.cantidad + delta;
    if (nuevaCantidad > 0 && nuevaCantidad <= producto.stock) {
        producto.cantidad = nuevaCantidad;
        producto.subtotal = producto.precio * nuevaCantidad;
        window.renderProductosVenta();
        window.updateTotales();
    }
};

window.updateCantidadDirecta = function(productoId, nuevaCantidad) {
    const producto = window.appState.productos.find(p => p.id === productoId);
    if (!producto) return;

    nuevaCantidad = parseInt(nuevaCantidad);
    if (nuevaCantidad > 0 && nuevaCantidad <= producto.stock) {
        producto.cantidad = nuevaCantidad;
        producto.subtotal = producto.precio * nuevaCantidad;
        window.renderProductosVenta();
        window.updateTotales();
    }
};

window.removeProducto = function(productoId) {
    window.appState.productos = window.appState.productos.filter(p => p.id !== productoId);
    window.renderProductosVenta();
    window.updateTotales();
};

window.seleccionarProducto = function(producto) {
    const productoParaAgregar = {
        id: producto.id,
        nombre: producto.nombre,
        precio: parseFloat(producto.precio),
        stock: parseInt(producto.stock),
        cantidad: 1,
        subtotal: parseFloat(producto.precio)
    };
    
    window.agregarProducto(productoParaAgregar);
    document.getElementById('resultados-busqueda').classList.add('d-none');
    document.getElementById('producto-search').value = '';
};

window.agregarProducto = function(producto) {
    console.log('Agregando producto:', producto); // Para debugging
    
    const existingIndex = window.appState.productos.findIndex(p => p.id === producto.id);
    
    if (existingIndex >= 0) {
        const nuevaCantidad = window.appState.productos[existingIndex].cantidad + producto.cantidad;
        if (nuevaCantidad <= producto.stock) {
            window.appState.productos[existingIndex].cantidad = nuevaCantidad;
            window.appState.productos[existingIndex].subtotal = 
                window.appState.productos[existingIndex].precio * nuevaCantidad;
        } else {
            window.showAlert('No hay suficiente stock disponible', 'warning');
            return;
        }
    } else {
        if (producto.cantidad <= producto.stock) {
            window.appState.productos.push({
                ...producto,
                subtotal: producto.precio * producto.cantidad
            });
        } else {
            window.showAlert('No hay suficiente stock disponible', 'warning');
            return;
        }
    }
    
    window.renderProductosVenta();
    window.updateTotales();
};

// Función para mostrar alertas
window.showAlert = function(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.querySelector('.container').insertAdjacentElement('afterbegin', alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
};

document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos DOM
    const elements = {
        searchInput: document.getElementById('producto-search'),
        searchResults: document.getElementById('resultados-busqueda'),
        productosTable: document.getElementById('productos-venta')?.querySelector('tbody'),
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
    initializeApp();
    setupEventListeners();

    function initializeApp() {
        updateVisibility();
        setupProductQuantityControls();
    }

    function setupEventListeners() {
        // Event listeners para productos disponibles
        document.querySelectorAll('.agregar-producto').forEach(btn => {
            btn.addEventListener('click', function() {
                const cardBody = this.closest('.card-body');
                const cantidadInput = cardBody.querySelector('.cantidad-input');
                const cantidad = parseInt(cantidadInput.value) || 1;
                
                const producto = {
                    id: parseInt(this.dataset.id),
                    nombre: this.dataset.nombre,
                    precio: parseFloat(this.dataset.precio),
                    stock: parseInt(this.dataset.cantidad),
                    cantidad: cantidad,
                    subtotal: parseFloat(this.dataset.precio) * cantidad
                };
                
                window.agregarProducto(producto);
                cantidadInput.value = 1;
            });
        });
    
        // Agregar los event listeners para los botones + y - de las cantidades
        document.querySelectorAll('.btn-decrease').forEach(btn => {
            btn.addEventListener('click', function() {
                const input = this.parentElement.querySelector('.cantidad-input');
                const currentValue = parseInt(input.value) || 1;
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                }
            });
        });
    
        document.querySelectorAll('.btn-increase').forEach(btn => {
            btn.addEventListener('click', function() {
                const input = this.parentElement.querySelector('.cantidad-input');
                const currentValue = parseInt(input.value) || 1;
                const maxValue = parseInt(input.getAttribute('max'));
                if (currentValue < maxValue) {
                    input.value = currentValue + 1;
                }
            });
        });
    
        // Event listener para búsqueda
        if (elements.searchInput) {
            elements.searchInput.addEventListener('input', handleSearch);
        }
    
        // Event listener para finalizar venta
        if (elements.finalizarBtn) {
            elements.finalizarBtn.addEventListener('click', handleFinalizarVenta);
        }
    
        // Event listener para cerrar resultados de búsqueda
        document.addEventListener('click', handleClickOutside);
    }

    function setupProductQuantityControls() {
        document.querySelectorAll('.cantidad-input').forEach(input => {
            input.addEventListener('change', function() {
                const value = parseInt(this.value) || 0;
                const max = parseInt(this.getAttribute('max'));
                if (value < 1) this.value = 1;
                if (value > max) this.value = max;
            });
        });
    }

    // Renderizar productos en la venta
    window.renderProductosVenta = function() {
        if (!elements.productosTable) return;
        
        elements.productosTable.innerHTML = window.appState.productos.map(producto => `
            <tr>
                <td>${producto.nombre}</td>
                <td>$${producto.precio.toFixed(2)}</td>
                <td>${producto.stock}</td>
                <td>
                    <div class="input-group input-group-sm" style="width: 120px;">
                        <button type="button" class="btn btn-outline-secondary btn-decrease" 
                                onclick="window.updateCantidad(${producto.id}, -1)">-</button>
                        <input type="number" class="form-control text-center cantidad-producto" 
                               value="${producto.cantidad}" 
                               min="1" 
                               max="${producto.stock}"
                               onchange="window.updateCantidadDirecta(${producto.id}, this.value)">
                        <button type="button" class="btn btn-outline-secondary btn-increase" 
                                onclick="window.updateCantidad(${producto.id}, 1)">+</button>
                    </div>
                </td>
                <td>$${producto.subtotal.toFixed(2)}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger" 
                            onclick="window.removeProducto(${producto.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
        updateVisibility();
    };

    // Actualizar totales
    window.updateTotales = function() {
        const subtotal = window.appState.productos.reduce((sum, p) => sum + p.subtotal, 0);
        const iva = subtotal * 0.16;
        const total = subtotal + iva - window.appState.descuento;

        if (elements.summarySubtotal) 
            elements.summarySubtotal.textContent = `$${subtotal.toFixed(2)}`;
        if (elements.summaryIva) 
            elements.summaryIva.textContent = `$${iva.toFixed(2)}`;
        if (elements.summaryTotal) 
            elements.summaryTotal.textContent = `$${total.toFixed(2)}`;
        if (elements.totalItems) 
            elements.totalItems.textContent = `${window.appState.productos.length} items`;
        
        if (elements.productosJson) {
            elements.productosJson.value = JSON.stringify(window.appState.productos);
        }
    };

    function updateVisibility() {
        if (!elements.productosTable || !elements.noProductos) return;
        
        if (window.appState.productos.length === 0) {
            elements.noProductos.classList.remove('d-none');
            elements.productosTable.closest('.table-responsive').classList.add('d-none');
        } else {
            elements.noProductos.classList.add('d-none');
            elements.productosTable.closest('.table-responsive').classList.remove('d-none');
        }
    }

    function clearSearchResults() {
        if (!elements.searchResults) return;
        elements.searchResults.innerHTML = '';
        elements.searchResults.classList.add('d-none');
    }

    async function buscarProductos(query) {
        try {
            const response = await fetch(`/api/productos/buscar?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            window.appState.busquedaResultados = data;
            renderSearchResults();
        } catch (error) {
            console.error('Error:', error);
            window.showAlert('Error al buscar productos', 'danger');
        }
    }

    async function handleFinalizarVenta(e) {
        e.preventDefault();
        
        if (window.appState.productos.length === 0) {
            window.showAlert('Agregue productos a la venta', 'warning');
            return;
        }

        if (!elements.metodoPago.value) {
            window.showAlert('Seleccione un método de pago', 'warning');
            return;
        }

        const ventaData = {
            productos: window.appState.productos,
            cliente_id: elements.clienteInput.value || null,
            metodo_pago: elements.metodoPago.value,
            subtotal: parseFloat(elements.summarySubtotal.textContent.replace('$', '')),
            iva: parseFloat(elements.summaryIva.textContent.replace('$', '')),
            total: parseFloat(elements.summaryTotal.textContent.replace('$', '')),
            descuento: window.appState.descuento
        };

        try {
            elements.finalizarBtn.disabled = true;
            elements.finalizarBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Procesando...';

            const response = await fetch(elements.formVenta.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(ventaData)
            });

            const data = await response.json();

            if (data.success) {
                window.showAlert('Venta registrada exitosamente', 'success');
                setTimeout(() => {
                    window.location.href = '/ventas';
                }, 1500);
            } else {
                throw new Error(data.message || 'Error al procesar la venta');
            }
        } catch (error) {
            handleVentaError(error);
        }
    }

    function handleVentaError(error) {
        console.error('Error:', error);
        window.showAlert(error.message || 'Error de conexión. Intente nuevamente.', 'danger');
        elements.finalizarBtn.disabled = false;
        elements.finalizarBtn.innerHTML = '<i class="fas fa-check me-2"></i> Finalizar Venta';
    }

    function handleSearch(e) {
        const query = e.target.value.trim();
        if (query.length >= 2) {
            buscarProductos(query);
        } else {
            clearSearchResults();
        }
    }

    function handleClickOutside(e) {
        if (!elements.searchResults?.contains(e.target) && 
            !elements.searchInput?.contains(e.target)) {
            clearSearchResults();
        }
    }

    function renderSearchResults() {
        if (!elements.searchResults) return;

        if (window.appState.busquedaResultados.length === 0) {
            elements.searchResults.innerHTML = '<div class="p-3">No se encontraron productos</div>';
        } else {
            elements.searchResults.innerHTML = window.appState.busquedaResultados.map(producto => `
                <div class="search-result-item p-2 border-bottom" role="button" 
                     onclick="window.seleccionarProducto(${JSON.stringify(producto).replace(/"/g, '&quot;')})">
                    <div class="d-flex justify-content-between">
                        <span>${producto.nombre}</span>
                        <span class="text-primary">$${producto.precio.toFixed(2)}</span>
                    </div>
                    <small class="text-muted">Stock: ${producto.stock}</small>
                </div>
            `).join('');
        }

        elements.searchResults.classList.remove('d-none');
    }
}
 );