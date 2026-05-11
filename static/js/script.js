/**
 * QI Manager – Interactive Dashboard JavaScript
 * Version: 2.0.0
 */

(function ($) {
    'use strict';

    var QI = {
        init: function () {
            this._initSidebar();
            this._initTopbar();
            this._initDataTables();
            this._initForms();
            this._initModals();
            this._initNotifications();
            this._initScrollTop();
            this._initTooltips();
        },

        /* ================================
           SIDEBAR
           ================================ */
        _initSidebar: function () {
            var self = this;

            // Toggle sidebar on mobile
            $('#sidebarToggle').on('click', function (e) {
                e.preventDefault();
                var sidebar = $('#sidebar');
                var overlay = $('#sidebarOverlay');

                sidebar.toggleClass('show');
                if (overlay.length) {
                    overlay.toggleClass('show');
                } else {
                    $('body').append('<div id="sidebarOverlay" class="sidebar-overlay"></div>');
                    $('#sidebarOverlay').addClass('show').on('click', function () {
                        sidebar.removeClass('show');
                        $(this).removeClass('show');
                    });
                }
            });

            // Close sidebar on outside click (mobile)
            $(document).on('click', function (e) {
                if ($(window).width() <= 768) {
                    var sidebar = $('#sidebar');
                    if (!sidebar.is(e.target) && sidebar.has(e.target).length === 0 &&
                        !$('#sidebarToggle').is(e.target) && $('#sidebarToggle').has(e.target).length === 0) {
                        sidebar.removeClass('show');
                        $('#sidebarOverlay').removeClass('show');
                    }
                }
            });

            // Close sidebar on resize to desktop
            $(window).on('resize', function () {
                if ($(window).width() > 768) {
                    $('#sidebar').removeClass('show');
                    $('#sidebarOverlay').removeClass('show');
                }
            });

            // Active link highlighting
            var path = window.location.pathname;
            $('.nav-link').each(function () {
                var href = $(this).attr('href');
                if (href && href !== '#' && path.indexOf(href) === 0) {
                    $(this).addClass('active').closest('.nav-section-title').prevAll('.active').removeClass('active');
                }
            });
        },

        /* ================================
           TOPBAR
           ================================ */
        _initTopbar: function () {
            // Dropdown toggle
            $(document).on('click', function (e) {
                var target = $(e.target);
                if (!target.closest('.dropdown').length) {
                    $('.dropdown-menu').removeClass('show');
                }
            });

            $('.dropdown > a').on('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                var menu = $(this).siblings('.dropdown-menu');
                $('.dropdown-menu').not(menu).removeClass('show');
                menu.toggleClass('show');
            });
        },

        /* ================================
           DATA TABLES
           ================================ */
        _initDataTables: function () {
            // User table
            if ($.fn.DataTable.isDataTable('#usersTable')) {
                $('#usersTable').DataTable().destroy();
            }
            $('#usersTable').DataTable({
                responsive: true,
                lengthChange: true,
                autoWidth: false,
                pageLength: 10,
                language: {
                    search: '<div class="d-flex align-items-center"><i class="fas fa-search me-2 text-muted"></i><input type="text" class="form-control form-control-sm" placeholder="Search users..."></div>',
                    searchPlaceholder: '',
                    lengthMenu: 'Show _MENU_',
                    info: 'Showing _START_ to _END_ of _TOTAL_ entries',
                    infoEmpty: 'No entries found',
                    infoFiltered: '(filtered from _MAX_ total)',
                    zeroRecords: '<div class="text-center py-4 text-muted">No matching records found</div>',
                    paginate: {
                        first: '<i class="fas fa-angle-double-left"></i>',
                        last: '<i class="fas fa-angle-double-right"></i>',
                        next: '<i class="fas fa-angle-right"></i>',
                        previous: '<i class="fas fa-angle-left"></i>'
                    }
                },
                dom: '<"top d-flex justify-content-between align-items-center mb-3"<"d-flex align-items-center"l><"d-flex"f>>rt<"bottom d-flex justify-content-between align-items-center mt-3"<"d-flex align-items-center"i><"d-flex"p>>',
                buttons: [
                    {
                        extend: 'copyHtml5',
                        text: '<i class="fas fa-copy"></i>',
                        titleAttr: 'Copy'
                    },
                    {
                        extend: 'csvHtml5',
                        text: '<i class="fas fa-file-csv"></i>',
                        titleAttr: 'CSV'
                    },
                    {
                        extend: 'excelHtml5',
                        text: '<i class="fas fa-file-excel"></i>',
                        titleAttr: 'Excel'
                    },
                    {
                        extend: 'pdfHtml5',
                        text: '<i class="fas fa-file-pdf"></i>',
                        titleAttr: 'PDF'
                    }
                ]
            });

            // Roles table
            if ($.fn.DataTable.isDataTable('#rolesTable')) {
                $('#rolesTable').DataTable().destroy();
            }
            $('#rolesTable').DataTable({
                responsive: true,
                lengthChange: true,
                autoWidth: false,
                pageLength: 10,
                language: {
                    search: '<div class="d-flex align-items-center"><i class="fas fa-search me-2 text-muted"></i><input type="text" class="form-control form-control-sm" placeholder="Search roles..."></div>',
                    searchPlaceholder: '',
                    lengthMenu: 'Show _MENU_',
                    info: 'Showing _START_ to _END_ of _TOTAL_ entries',
                    infoEmpty: 'No entries found',
                    infoFiltered: '(filtered from _MAX_ total)',
                    zeroRecords: '<div class="text-center py-4 text-muted">No matching records found</div>',
                    paginate: {
                        first: '<i class="fas fa-angle-double-left"></i>',
                        last: '<i class="fas fa-angle-double-right"></i>',
                        next: '<i class="fas fa-angle-right"></i>',
                        previous: '<i class="fas fa-angle-left"></i>'
                    }
                },
                dom: '<"top d-flex justify-content-between align-items-center mb-3"<"d-flex align-items-center"l><"d-flex"f>>rt<"bottom d-flex justify-content-between align-items-center mt-3"<"d-flex align-items-center"i><"d-flex"p>>',
                buttons: [
                    {
                        extend: 'copyHtml5',
                        text: '<i class="fas fa-copy"></i>',
                        titleAttr: 'Copy'
                    },
                    {
                        extend: 'csvHtml5',
                        text: '<i class="fas fa-file-csv"></i>',
                        titleAttr: 'CSV'
                    },
                    {
                        extend: 'pdfHtml5',
                        text: '<i class="fas fa-file-pdf"></i>',
                        titleAttr: 'PDF'
                    }
                ]
            });

            // Permissions table
            if ($.fn.DataTable.isDataTable('#permissionsTable')) {
                $('#permissionsTable').DataTable().destroy();
            }
            $('#permissionsTable').DataTable({
                responsive: true,
                lengthChange: true,
                autoWidth: false,
                pageLength: 10,
                language: {
                    search: '<div class="d-flex align-items-center"><i class="fas fa-search me-2 text-muted"></i><input type="text" class="form-control form-control-sm" placeholder="Search permissions..."></div>',
                    searchPlaceholder: '',
                    lengthMenu: 'Show _MENU_',
                    info: 'Showing _START_ to _END_ of _TOTAL_ entries',
                    infoEmpty: 'No entries found',
                    infoFiltered: '(filtered from _MAX_ total)',
                    zeroRecords: '<div class="text-center py-4 text-muted">No matching records found</div>',
                    paginate: {
                        first: '<i class="fas fa-angle-double-left"></i>',
                        last: '<i class="fas fa-angle-double-right"></i>',
                        next: '<i class="fas fa-angle-right"></i>',
                        previous: '<i class="fas fa-angle-left"></i>'
                    }
                },
                dom: '<"top d-flex justify-content-between align-items-center mb-3"<"d-flex align-items-center"l><"d-flex"f>>rt<"bottom d-flex justify-content-between align-items-center mt-3"<"d-flex align-items-center"i><"d-flex"p>>',
                buttons: [
                    {
                        extend: 'copyHtml5',
                        text: '<i class="fas fa-copy"></i>',
                        titleAttr: 'Copy'
                    },
                    {
                        extend: 'csvHtml5',
                        text: '<i class="fas fa-file-csv"></i>',
                        titleAttr: 'CSV'
                    }
                ]
            });
        },

        /* ================================
           FORMS
           ================================ */
        _initForms: function () {
            // Select all checkboxes in forms
            $('.select-all').on('change', function () {
                var checked = $(this).prop('checked');
                $(this).closest('.form-group').find('input[type="checkbox"]').not(this).prop('checked', checked);
            });

            // Confirm checkbox
            $('#deleteConfirm').on('change', function () {
                var btn = $(this).closest('.modal-body').siblings('.modal-footer').find('.btn-danger');
                if ($(this).prop('checked')) {
                    btn.removeAttr('disabled');
                } else {
                    btn.attr('disabled', 'disabled');
                }
            });
        },

        /* ================================
           MODALS & SWEETALERT
           ================================ */
        _initModals: function () {
            // Auto-close alerts after 5 seconds
            setTimeout(function () {
                $('.alert').fadeOut('slow', function () {
                    $(this).remove();
                });
            }, 5000);
        },

        /* ================================
           NOTIFICATIONS (Toast)
           ================================ */
        _initNotifications: function () {
            // Show toast from data attributes
            $('[data-toast-message]').each(function () {
                var $this = $(this);
                QI.showToast(
                    $this.data('toast-message'),
                    $this.data('toast-type') || 'success',
                    $this.data('toast-title') || ''
                );
            });

            // Convert Bootstrap alerts to toasts
            $('.alert').each(function () {
                var $alert = $(this);
                var alertClass = $alert.attr('class') || '';
                var type = 'success';

                if (alertClass.indexOf('alert-danger') !== -1) {
                    type = 'error';
                } else if (alertClass.indexOf('alert-warning') !== -1) {
                    type = 'warning';
                } else if (alertClass.indexOf('alert-info') !== -1) {
                    type = 'info';
                }

                QI.showToast($alert.text().trim(), type);
                $alert.hide();
            });
        },

        showToast: function (message, type, title) {
            type = type || 'success';
            title = title || '';

            var iconMap = {
                'success': 'success',
                'error': 'error',
                'danger': 'error',
                'warning': 'warning',
                'info': 'info'
            };

            Swal.fire({
                toast: true,
                position: 'top-end',
                icon: iconMap[type] || 'success',
                title: title || message,
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer);
                    toast.addEventListener('mouseleave', Swal.resumeTimer);
                }
            });
        },

        confirmDelete: function (options) {
            options = $.extend({
                title: 'Are you sure?',
                text: 'This action cannot be undone.',
                confirmText: 'Yes, delete it!',
                cancelText: 'Cancel'
            }, options);

            return Swal.fire({
                title: options.title,
                text: options.text,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: '<i class="fas fa-trash me-2"></i>' + options.confirmText,
                cancelButtonText: '<i class="fas fa-times me-2"></i>' + options.cancelText
            });
        },

        showSuccess: function (message) {
            Swal.fire({
                icon: 'success',
                title: 'Success!',
                text: message,
                timer: 2000,
                showConfirmButton: false
            });
        },

        showError: function (message) {
            Swal.fire({
                icon: 'error',
                title: 'Error!',
                text: message,
                timer: 3000,
                showConfirmButton: false
            });
        },

        /* ================================
           SCROLL TO TOP
           ================================ */
        _initScrollTop: function () {
            var scrollBtn = $('#scrollTop');

            $(window).on('scroll', function () {
                if ($(this).scrollTop() > 300) {
                    scrollBtn.addClass('visible');
                } else {
                    scrollBtn.removeClass('visible');
                }
            });

            scrollBtn.on('click', function (e) {
                e.preventDefault();
                $('html, body').animate({ scrollTop: 0 }, 600, 'easeInOutCubic');
            });
        },

        /* ================================
           TOOLTIPS
           ================================ */
        _initTooltips: function () {
            $('[data-bs-toggle="tooltip"]').tooltip();
            $('[data-toggle="popover"]').popover();
        }
    };

    // Initialize on document ready
    $(document).ready(function () {
        QI.init();
    });

    // Expose QI object globally
    window.QI = QI;

})(jQuery);