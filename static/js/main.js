/* ============================================================
   SPADA UMG - Main JavaScript
   ============================================================ */

(function() {
    'use strict';

    // ============================================================
    // 1. DARK MODE
    // ============================================================
    function initDarkMode() {
        const stored = localStorage.getItem('darkMode');
        if (stored === null) {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            localStorage.setItem('darkMode', prefersDark);
        }
        const isDark = localStorage.getItem('darkMode') === 'true';
        if (isDark) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }

    function toggleDarkMode() {
        const isDark = localStorage.getItem('darkMode') === 'true';
        localStorage.setItem('darkMode', !isDark);
        document.documentElement.classList.toggle('dark', !isDark);
        document.cookie = 'theme_preference=' + (!isDark ? 'dark' : 'light') + ';path=/';
    }

    // ============================================================
    // 2. MOBILE SIDEBAR
    // ============================================================
    function initMobileSidebar() {
        const sidebar = document.querySelector('aside');
        const toggleBtn = document.querySelector('[aria-label="Toggle sidebar"]');
        const backdrop = document.querySelector('.fixed.inset-0.bg-black\\/50');

        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener('click', function() {
                const isOpen = sidebar.classList.contains('translate-x-0');
                sidebar.classList.toggle('translate-x-0', !isOpen);
                sidebar.classList.toggle('-translate-x-full', isOpen);
                document.body.classList.toggle('overflow-hidden', !isOpen && window.innerWidth < 768);
            });
        }

        if (backdrop) {
            backdrop.addEventListener('click', function() {
                sidebar.classList.remove('translate-x-0');
                sidebar.classList.add('-translate-x-full');
                document.body.classList.remove('overflow-hidden');
            });
        }

        window.addEventListener('resize', function() {
            if (window.innerWidth >= 1024) {
                document.body.classList.remove('overflow-hidden');
            }
        });
    }

    // ============================================================
    // 3. FORM VALIDATION
    // ============================================================
    function initFormValidation() {
        document.querySelectorAll('form[data-validate]').forEach(function(form) {
            form.addEventListener('submit', function(e) {
                let isValid = true;
                const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');

                inputs.forEach(function(input) {
                    const errorEl = input.parentElement.querySelector('.form-error') || 
                                    input.closest('.form-group')?.querySelector('.form-error');
                    
                    if (errorEl) {
                        errorEl.textContent = '';
                        errorEl.classList.add('hidden');
                    }
                    
                    input.classList.remove('form-input-error');

                    if (!input.value.trim()) {
                        isValid = false;
                        input.classList.add('form-input-error');
                        const label = form.querySelector(`label[for="${input.id}"]`)?.textContent || 'Field ini';
                        showFieldError(input, `${label} wajib diisi.`);
                    } else if (input.type === 'email' && !isValidEmail(input.value)) {
                        isValid = false;
                        input.classList.add('form-input-error');
                        showFieldError(input, 'Format email tidak valid.');
                    } else if (input.type === 'password' && input.dataset.minLength && input.value.length < parseInt(input.dataset.minLength)) {
                        isValid = false;
                        input.classList.add('form-input-error');
                        showFieldError(input, `Minimal ${input.dataset.minLength} karakter.`);
                    } else if (input.dataset.match) {
                        const matchInput = document.getElementById(input.dataset.match);
                        if (matchInput && input.value !== matchInput.value) {
                            isValid = false;
                            input.classList.add('form-input-error');
                            showFieldError(input, 'Konfirmasi tidak cocok.');
                        }
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                    const firstError = form.querySelector('.form-input-error');
                    if (firstError) {
                        firstError.focus();
                        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            });
        });
    }

    function showFieldError(input, message) {
        let errorEl = input.parentElement.querySelector('.form-error') || 
                      input.closest('.form-group')?.querySelector('.form-error');
        
        if (!errorEl) {
            errorEl = document.createElement('p');
            errorEl.className = 'form-error';
            input.parentElement.appendChild(errorEl);
        }
        
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // Real-time validation on blur
    document.addEventListener('blur', function(e) {
        const input = e.target;
        if (input.hasAttribute('required') && input.closest('form[data-validate]')) {
            const errorEl = input.parentElement.querySelector('.form-error') || 
                           input.closest('.form-group')?.querySelector('.form-error');
            
            if (errorEl) {
                errorEl.textContent = '';
                errorEl.classList.add('hidden');
            }
            input.classList.remove('form-input-error');

            if (!input.value.trim()) {
                input.classList.add('form-input-error');
                const label = document.querySelector(`label[for="${input.id}"]`)?.textContent || 'Field ini';
                showFieldError(input, `${label} wajib diisi.`);
            } else if (input.type === 'email' && !isValidEmail(input.value)) {
                input.classList.add('form-input-error');
                showFieldError(input, 'Format email tidak valid.');
            }
        }
    }, true);

    // ============================================================
    // 4. FILE UPLOAD PREVIEW
    // ============================================================
    function initFileUploadPreview() {
        document.addEventListener('change', function(e) {
            if (e.target.type === 'file' && e.target.dataset.preview) {
                const previewContainer = document.getElementById(e.target.dataset.preview);
                if (!previewContainer) return;

                previewContainer.innerHTML = '';
                const files = Array.from(e.target.files);
                const maxPreview = parseInt(e.target.dataset.maxPreview) || 5;
                const filesToShow = files.slice(0, maxPreview);

                filesToShow.forEach(function(file) {
                    const reader = new FileReader();
                    reader.onload = function(ev) {
                        const previewItem = document.createElement('div');
                        previewItem.className = 'file-preview';

                        if (file.type.startsWith('image/')) {
                            previewItem.innerHTML = `
                                <img src="${ev.target.result}" alt="${file.name}">
                                <span class="text-xs truncate max-w-[120px]">${file.name}</span>
                                <span class="text-xs text-gray-400">(${formatFileSize(file.size)})</span>
                                <button type="button" class="file-preview-remove" data-filename="${file.name}">
                                    <i class="fas fa-times"></i>
                                </button>
                            `;
                        } else {
                            const icon = getFileIcon(file.name);
                            previewItem.innerHTML = `
                                <div class="h-10 w-10 rounded bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                                    <i class="${icon} text-gray-500 dark:text-gray-300"></i>
                                </div>
                                <span class="text-xs truncate max-w-[120px]">${file.name}</span>
                                <span class="text-xs text-gray-400">(${formatFileSize(file.size)})</span>
                                <button type="button" class="file-preview-remove" data-filename="${file.name}">
                                    <i class="fas fa-times"></i>
                                </button>
                            `;
                        }

                        previewContainer.appendChild(previewItem);

                        previewItem.querySelector('.file-preview-remove').addEventListener('click', function() {
                            previewItem.remove();
                            e.target.value = '';
                            const dt = new DataTransfer();
                            const remainingFiles = Array.from(e.target.files).filter(f => f.name !== this.dataset.filename);
                            remainingFiles.forEach(f => dt.items.add(f));
                            e.target.files = dt.files;
                        });
                    };
                    reader.readAsDataURL(file);
                });

                if (files.length > maxPreview) {
                    const more = document.createElement('p');
                    more.className = 'text-xs text-gray-400 mt-2';
                    more.textContent = `+${files.length - maxPreview} file lainnya`;
                    previewContainer.appendChild(more);
                }
            }
        });

        // File input label update
        document.addEventListener('change', function(e) {
            if (e.target.type === 'file' && e.target.dataset.label) {
                const label = document.getElementById(e.target.dataset.label);
                if (label) {
                    const count = e.target.files.length;
                    if (count === 0) {
                        label.innerHTML = '<i class="fas fa-upload mr-2"></i> Pilih File';
                    } else if (count === 1) {
                        label.textContent = e.target.files[0].name;
                    } else {
                        label.textContent = `${count} file dipilih`;
                    }
                }
            }
        });
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    function getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            pdf: 'fas fa-file-pdf text-red-500',
            doc: 'fas fa-file-word text-blue-500',
            docx: 'fas fa-file-word text-blue-500',
            xls: 'fas fa-file-excel text-green-500',
            xlsx: 'fas fa-file-excel text-green-500',
            ppt: 'fas fa-file-powerpoint text-orange-500',
            pptx: 'fas fa-file-powerpoint text-orange-500',
            zip: 'fas fa-file-archive text-yellow-500',
            rar: 'fas fa-file-archive text-yellow-500',
            '7z': 'fas fa-file-archive text-yellow-500',
            mp4: 'fas fa-file-video text-purple-500',
            avi: 'fas fa-file-video text-purple-500',
            mov: 'fas fa-file-video text-purple-500',
            mp3: 'fas fa-file-audio text-indigo-500',
            wav: 'fas fa-file-audio text-indigo-500',
            jpg: 'fas fa-file-image text-cyan-500',
            jpeg: 'fas fa-file-image text-cyan-500',
            png: 'fas fa-file-image text-cyan-500',
            gif: 'fas fa-file-image text-cyan-500',
            svg: 'fas fa-file-image text-cyan-500',
        };
        return icons[ext] || 'fas fa-file text-gray-400';
    }

    // ============================================================
    // 5. AUTO-DISMISS ALERTS
    // ============================================================
    function initAutoDismissAlerts() {
        document.querySelectorAll('[data-auto-dismiss]').forEach(function(alert) {
            const delay = parseInt(alert.dataset.autoDismiss) || 5000;
            setTimeout(function() {
                alert.style.transition = 'all 0.3s ease-out';
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(function() {
                    alert.remove();
                }, 300);
            }, delay);
        });
    }

    // ============================================================
    // 6. SCROLL TO TOP
    // ============================================================
    function initScrollToTop() {
        const scrollBtn = document.getElementById('scroll-to-top');
        if (!scrollBtn) return;

        window.addEventListener('scroll', function() {
            if (window.scrollY > 400) {
                scrollBtn.classList.remove('hidden');
            } else {
                scrollBtn.classList.add('hidden');
            }
        }, { passive: true });

        scrollBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // ============================================================
    // 7. CHARACTER COUNTER
    // ============================================================
    function initCharCounters() {
        document.querySelectorAll('[data-charcount]').forEach(function(textarea) {
            const counter = document.getElementById(textarea.dataset.charcount);
            if (!counter) return;

            const maxLength = textarea.getAttribute('maxlength');
            
            function updateCount() {
                const current = textarea.value.length;
                counter.textContent = maxLength ? `${current}/${maxLength}` : current.toString();
            }

            textarea.addEventListener('input', updateCount);
            updateCount();
        });
    }

    // ============================================================
    // 8. PASSWORD TOGGLE
    // ============================================================
    function initPasswordToggle() {
        document.querySelectorAll('[data-password-toggle]').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const target = document.getElementById(this.dataset.passwordToggle);
                if (!target) return;

                const type = target.type === 'password' ? 'text' : 'password';
                target.type = type;
                
                const icon = this.querySelector('i');
                if (icon) {
                    icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
                }
            });
        });
    }

    // ============================================================
    // 9. CONFIRM DIALOG
    // ============================================================
    function initConfirmDialogs() {
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('[data-confirm]');
            if (!btn) return;

            e.preventDefault();
            const message = btn.dataset.confirm || 'Apakah Anda yakin?';
            
            if (confirm(message)) {
                if (btn.tagName === 'A') {
                    window.location.href = btn.href;
                } else if (btn.tagName === 'BUTTON' || btn.type === 'submit') {
                    btn.closest('form')?.submit();
                }
            }
        });
    }

    // ============================================================
    // 10. TOOLTIP INITIALIZATION
    // ============================================================
    function initTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(function(el) {
            el.addEventListener('mouseenter', function() {
                const text = this.dataset.tooltip;
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip animate-fade-in';
                tooltip.textContent = text;

                const rect = this.getBoundingClientRect();
                tooltip.style.left = rect.left + rect.width / 2 + 'px';
                tooltip.style.top = rect.bottom + 8 + 'px';
                tooltip.style.transform = 'translateX(-50%)';
                
                document.body.appendChild(tooltip);

                this.addEventListener('mouseleave', function() {
                    tooltip.remove();
                }, { once: true });
            });
        });
    }

    // ============================================================
    // 11. HTMX GLOBAL CONFIG
    // ============================================================
    function initHtmxConfig() {
        if (typeof htmx !== 'undefined') {
            htmx.config.defaultSwapStyle = 'innerHTML';
            htmx.config.swapDelay = 100;
            htmx.config.scrollIntoViewOnBoost = true;

            document.addEventListener('htmx:afterSettle', function(evt) {
                initTooltips();
                initCharCounters();
                initAutoDismissAlerts();
            });

            document.addEventListener('htmx:beforeSwap', function(evt) {
                if (evt.detail.xhr.status >= 400) {
                    evt.detail.shouldSwap = false;
                    console.error('HTMX error:', evt.detail.xhr.status, evt.detail.xhr.responseText);
                }
            });
        }
    }

    // ============================================================
    // 12. GLOBAL SEARCH KEYBOARD SHORTCUT
    // ============================================================
    function initSearchShortcut() {
        document.addEventListener('keydown', function(e) {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                const searchModal = document.querySelector('[x-data]');
                if (searchModal && searchModal.__x) {
                    searchModal.__x.$data.searchOpen = true;
                    setTimeout(function() {
                        const input = document.getElementById('global-search-input');
                        if (input) input.focus();
                    }, 100);
                }
            }
            if (e.key === 'Escape') {
                const searchModal = document.querySelector('[x-data]');
                if (searchModal && searchModal.__x) {
                    searchModal.__x.$data.searchOpen = false;
                }
            }
        });
    }

    // ============================================================
    // 13. AUTO-RESIZE TEXTAREA
    // ============================================================
    function initAutoResizeTextarea() {
        document.addEventListener('input', function(e) {
            if (e.target.tagName === 'TEXTAREA' && e.target.dataset.autoResize !== undefined) {
                e.target.style.height = 'auto';
                e.target.style.height = e.target.scrollHeight + 'px';
            }
        });
    }

    // ============================================================
    // 14. COPY TO CLIPBOARD
    // ============================================================
    function initClipboardButtons() {
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('[data-clipboard]');
            if (!btn) return;

            const text = btn.dataset.clipboard;
            navigator.clipboard.writeText(text).then(function() {
                const original = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check text-green-500"></i>';
                btn.classList.add('text-green-500');
                setTimeout(function() {
                    btn.innerHTML = original;
                    btn.classList.remove('text-green-500');
                }, 2000);
            }).catch(function(err) {
                console.error('Clipboard error:', err);
            });
        });
    }

    // ============================================================
    // 15. TABLE ROW LINK
    // ============================================================
    function initTableRowLinks() {
        document.querySelectorAll('tr[data-href]').forEach(function(row) {
            row.addEventListener('click', function() {
                window.location.href = this.dataset.href;
            });
            row.style.cursor = 'pointer';
        });
    }

    // ============================================================
    // 16. RATE LIMITER FOR HTMX SEARCH
    // ============================================================
    function initSearchRateLimiter() {
        const searchInput = document.getElementById('global-search-input');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('keyup', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function() {
                    htmx.trigger(searchInput, 'keyup');
                }, 300);
            });
        }
    }

    // ============================================================
    // 17. ACTIVE NAV LINK HIGHLIGHT
    // ============================================================
    function initActiveNavHighlight() {
        const currentPath = window.location.pathname;
        document.querySelectorAll('nav a, .sidebar a').forEach(function(link) {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    // ============================================================
    // 18. NOTIFICATION POLLING
    // ============================================================
    function initNotificationPolling() {
        const notifBadge = document.querySelector('[x-data]');
        if (!notifBadge) return;

        setInterval(function() {
            const container = document.getElementById('notification-dropdown');
            if (container && typeof htmx !== 'undefined') {
                htmx.trigger(container, 'every:10s');
            }
        }, 10000);
    }

    // ============================================================
    // INITIALIZATION
    // ============================================================
    document.addEventListener('DOMContentLoaded', function() {
        initDarkMode();
        initMobileSidebar();
        initFormValidation();
        initFileUploadPreview();
        initAutoDismissAlerts();
        initScrollToTop();
        initCharCounters();
        initPasswordToggle();
        initConfirmDialogs();
        initTooltips();
        initHtmxConfig();
        initSearchShortcut();
        initAutoResizeTextarea();
        initClipboardButtons();
        initTableRowLinks();
        initSearchRateLimiter();
        initActiveNavHighlight();
        initNotificationPolling();

        console.log('%c SPADA UMG LMS ', 'background: #0070d1; color: white; font-size: 16px; font-weight: bold; padding: 8px 12px; border-radius: 4px;');
        console.log('%c Version 1.0 | Learning Management System ', 'color: #6b7280; font-size: 12px;');
    });

    // Re-initialize on HTMX content swap
    document.addEventListener('htmx:afterSwap', function() {
        initTooltips();
        initCharCounters();
        initAutoDismissAlerts();
        initConfirmDialogs();
        initClipboardButtons();
        initTableRowLinks();
        initFormValidation();
        initFileUploadPreview();
    });

    // Expose utilities globally
    window.SPADA = {
        toggleDarkMode: toggleDarkMode,
        formatFileSize: formatFileSize,
        getFileIcon: getFileIcon,
        isValidEmail: isValidEmail,
    };

})();
