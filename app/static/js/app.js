/**
 * Actividades Sky — JavaScript Principal
 * Funcionalidades interactivas del sistema.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ═══ SIDEBAR TOGGLE (Mobile) ═══
    window.toggleSidebar = function () {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('show');
        }
    };

    // Cerrar sidebar al hacer click fuera (mobile)
    document.addEventListener('click', function (e) {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.querySelector('.sidebar-toggle');
        if (sidebar && sidebar.classList.contains('show') &&
            !sidebar.contains(e.target) && !toggle.contains(e.target)) {
            sidebar.classList.remove('show');
        }
    });

    // ═══ CONFIRMACIÓN DE ELIMINACIÓN ═══
    document.querySelectorAll('.btn-delete').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const form = this.closest('form');

            Swal.fire({
                title: '¿Está seguro?',
                text: 'Esta acción no se puede deshacer.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#c62828',
                cancelButtonColor: '#455a64',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar',
                background: '#1a2052',
                color: '#e8eaf6'
            }).then(function (result) {
                if (result.isConfirmed) {
                    form.submit();
                }
            });
        });
    });

    // ═══ AUTO-DISMISS FLASH ALERTS ═══
    document.querySelectorAll('.flash-alert').forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // ═══ TOOLTIPS ═══
    var tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (el) {
        return new bootstrap.Tooltip(el);
    });

    // ═══ FORMATO MONEDA EN INPUTS ═══
    document.querySelectorAll('input[type="number"]').forEach(function (input) {
        input.addEventListener('wheel', function (e) {
            e.preventDefault();
        });
    });

    // ═══ FECHA ACTUAL POR DEFECTO ═══
    const fechaInputs = document.querySelectorAll('input[type="date"]:not([value])');
    const hoy = new Date().toISOString().split('T')[0];
    fechaInputs.forEach(function (input) {
        if (!input.value && !input.getAttribute('value')) {
            // Solo autocompletar si no tiene valor
        }
    });

});
