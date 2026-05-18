/**
 * QI Manager - Interactive Dashboard JavaScript
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

            $(window).on('resize', function () {
                if ($(window).width() > 768) {
                    $('#sidebar').removeClass('show');
                    $('#sidebarOverlay').removeClass('show');
                }
            });

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

            $(document).on('click', '.notification-dropdown .dropdown-item', function () {
                var $item = $(this);
                if (!$item.hasClass('dropdown-header') && !$item.closest('.dropdown-footer').length) {
                    $item.find('.notification-icon').removeClass('bg-primary').addClass('bg-green');
                }
            });
        },

        /* ================================
           DATA TABLES (Server-Side)
           ================================ */
        _initDataTables: function () {
            if (typeof $.fn.DataTable === 'undefined') {
                console.warn('QI: DataTables plugin not loaded.');
                return;
            }

            var self = this;

            // --- Users Table ---
            if ($('#usersTable').length) {
                if ($.fn.DataTable.isDataTable('#usersTable')) {
                    $('#usersTable').DataTable().destroy();
                }
                self._usersTable = $('#usersTable').DataTable({
                    processing: true,
                    serverSide: true,
                    ajax: {
                        url: $('#usersTable').data('ajax-url') || '/ajax/users-datatable/',
                        dataSrc: 'data'
                    },
                    responsive: true,
                    lengthChange: true,
                    autoWidth: false,
                    pageLength: 10,
                    order: [[1, 'desc']],
                    language: {
                        searchPlaceholder: 'Search users...',
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
                    columns: [
                        { data: null, orderable: false, render: function (data, type, row, meta) { return meta.row + 1; } },
                        {
                            data: null,
                            render: function (data, type, row) {
                                var initials = (row.username || '?').charAt(0).toUpperCase();
                                return '<div class="d-flex align-items-center">' +
                                    '<div class="avatar-sm avatar-rounded bg-primary bg-opacity-10 text-primary me-2" style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem;">' + initials + '</div>' +
                                    '<div><div class="fw-semibold">' + (row.full_name || row.username) + '</div><small class="text-muted">@' + row.username + '</small></div>' +
                                    '</div>';
                            }
                        },
                        { data: 'email' },
                        { data: 'roles' },
                        { data: 'is_active' },
                        {
                            data: null, orderable: false,
                            render: function (data, type, row) {
                                return '<div class="btn-group btn-group-sm">' +
                                    '<a href="/users/' + row.id + '/" class="btn btn-outline-info" data-bs-toggle="tooltip" title="View"><i class="fas fa-eye"></i></a>' +
                                    '<a href="/users/' + row.id + '/update/" class="btn btn-outline-warning" data-bs-toggle="tooltip" title="Edit"><i class="fas fa-edit"></i></a>' +
                                    '<button type="button" class="btn btn-outline-danger delete-user-btn" data-id="' + row.id + '" data-name="' + (row.full_name || row.username) + '" title="Delete"><i class="fas fa-trash"></i></button>' +
                                    '</div>';
                            }
                        }
                    ]
                });
            }

            // --- Roles Table ---
            if ($('#rolesTable').length) {
                if ($.fn.DataTable.isDataTable('#rolesTable')) {
                    $('#rolesTable').DataTable().destroy();
                }
                self._rolesTable = $('#rolesTable').DataTable({
                    processing: true,
                    serverSide: true,
                    ajax: {
                        url: $('#rolesTable').data('ajax-url') || '/ajax/roles-datatable/',
                        dataSrc: 'data'
                    },
                    responsive: true,
                    lengthChange: true,
                    autoWidth: false,
                    pageLength: 10,
                    order: [[1, 'asc']],
                    language: {
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
                    columns: [
                        { data: null, orderable: false, render: function (data, type, row, meta) { return meta.row + 1; } },
                        {
                            data: null,
                            render: function (data, type, row) {
                                var initials = (row.name || '?').charAt(0).toUpperCase();
                                return '<div class="d-flex align-items-center">' +
                                    '<div class="avatar-sm avatar-rounded bg-primary bg-opacity-10 text-primary me-2" style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem;">' + initials + '</div>' +
                                    '<div><div class="fw-semibold">' + row.name + '</div><small class="text-muted">' + (row.created_at || '') + '</small></div>' +
                                    '</div>';
                            }
                        },
                        { data: 'description' },
                        { data: 'permissions', render: function (data) { return data > 0 ? '<span class="badge bg-info-subtle text-info">' + data + ' perms</span>' : '<span class="badge bg-light text-muted">None</span>'; } },
                        { data: 'users', render: function (data) { return data > 0 ? '<span class="badge bg-success-subtle text-success">' + data + ' users</span>' : '<span class="badge bg-light text-muted">None</span>'; } },
                        {
                            data: null, orderable: false,
                            render: function (data, type, row) {
                                return '<div class="btn-group btn-group-sm">' +
                                    '<a href="/roles/' + row.id + '/" class="btn btn-outline-info" data-bs-toggle="tooltip" title="View"><i class="fas fa-eye"></i></a>' +
                                    '<a href="/roles/' + row.id + '/update/" class="btn btn-outline-warning" data-bs-toggle="tooltip" title="Edit"><i class="fas fa-edit"></i></a>' +
                                    '<button type="button" class="btn btn-outline-danger delete-role-btn" data-id="' + row.id + '" data-name="' + row.name + '" data-perms="' + row.permissions + '" data-users="' + row.users + '" title="Delete"><i class="fas fa-trash"></i></button>' +
                                    '</div>';
                            }
                        }
                    ]
                });
            }

            // --- Permissions Table ---
            if ($('#permissionsTable').length) {
                if ($.fn.DataTable.isDataTable('#permissionsTable')) {
                    $('#permissionsTable').DataTable().destroy();
                }
                self._permissionsTable = $('#permissionsTable').DataTable({
                    processing: true,
                    serverSide: true,
                    ajax: {
                        url: $('#permissionsTable').data('ajax-url') || '/ajax/permissions-datatable/',
                        dataSrc: 'data'
                    },
                    responsive: true,
                    lengthChange: true,
                    autoWidth: false,
                    pageLength: 10,
                    order: [[1, 'asc']],
                    language: {
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
                    columns: [
                        { data: null, orderable: false, render: function (data, type, row, meta) { return meta.row + 1; } },
                        { data: 'name' },
                        { data: 'codename', render: function (data) { return '<code class="bg-light px-2 py-1 rounded">' + data + '</code>'; } },
                        { data: 'description' },
                        { data: 'roles' },
                        {
                            data: null, orderable: false,
                            render: function (data, type, row) {
                                return '<div class="btn-group btn-group-sm">' +
                                    '<a href="/permissions/' + row.id + '/" class="btn btn-outline-info" data-bs-toggle="tooltip" title="View"><i class="fas fa-eye"></i></a>' +
                                    '<a href="/permissions/' + row.id + '/update/" class="btn btn-outline-warning" data-bs-toggle="tooltip" title="Edit"><i class="fas fa-edit"></i></a>' +
                                    '<button type="button" class="btn btn-outline-danger delete-permission-btn" data-id="' + row.id + '" data-name="' + row.name + '" data-codename="' + row.codename + '" title="Delete"><i class="fas fa-trash"></i></button>' +
                                    '</div>';
                            }
                        }
                    ]
                });
            }

            // --- Delete button handlers (event delegation for AJAX-rendered rows) ---
            $(document).on('click', '.delete-user-btn', function () {
                var id = $(this).data('id');
                var name = $(this).data('name');
                $('#deleteUserName').text(name);
                $('#deleteUserForm').attr('action', '/users/' + id + '/delete/');
                var modal = new bootstrap.Modal(document.getElementById('deleteUserModal'));
                modal.show();
            });

            $(document).on('click', '.delete-role-btn', function () {
                var id = $(this).data('id');
                var name = $(this).data('name');
                var perms = $(this).data('perms');
                var users = $(this).data('users');
                $('#deleteRoleName').text(name);
                var warning = '';
                if (users > 0) warning += 'This role has ' + users + ' user(s). ';
                if (perms > 0) warning += 'This role has ' + perms + ' permission(s).';
                $('#deleteRoleWarning').text(warning);
                $('#deleteRoleForm').attr('action', '/roles/' + id + '/delete/');
                var modal = new bootstrap.Modal(document.getElementById('deleteRoleModal'));
                modal.show();
            });

            $(document).on('click', '.delete-permission-btn', function () {
                var id = $(this).data('id');
                var name = $(this).data('name');
                var codename = $(this).data('codename');
                $('#deletePermName').text(name);
                $('#deletePermCodename').text(codename);
                $('#deletePermWarning').text('');
                $('#deletePermForm').attr('action', '/permissions/' + id + '/delete/');
                var modal = new bootstrap.Modal(document.getElementById('deletePermissionModal'));
                modal.show();
            });
        },

        /* ================================
           FORMS
           ================================ */
        _initForms: function () {
            $('.select-all').on('change', function () {
                var checked = $(this).prop('checked');
                $(this).closest('.form-group').find('input[type="checkbox"]').not(this).prop('checked', checked);
            });

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
            $('[data-toast-message]').each(function () {
                var $this = $(this);
                QI.showToast(
                    $this.data('toast-message'),
                    $this.data('toast-type') || 'success',
                    $this.data('toast-title') || ''
                );
            });

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
                didOpen: function (toast) {
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