/**
 * Main JavaScript file for the Library Management System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    var alertList = document.querySelectorAll('.alert');
    alertList.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm before deleting
    var deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Czy na pewno chcesz usunąć ten element? Tej operacji nie można cofnąć.')) {
                e.preventDefault();
            }
        });
    });
    
    // Toggle view between grid and list for book catalog
    const gridViewBtn = document.querySelector('.btn-grid-view');
    const listViewBtn = document.querySelector('.btn-list-view');
    const bookContainer = document.querySelector('.book-container');
    
    if (gridViewBtn && listViewBtn && bookContainer) {
        gridViewBtn.addEventListener('click', function() {
            bookContainer.classList.remove('list-view');
            bookContainer.classList.add('grid-view');
            gridViewBtn.classList.add('active');
            listViewBtn.classList.remove('active');
            localStorage.setItem('bookViewPreference', 'grid');
        });
        
        listViewBtn.addEventListener('click', function() {
            bookContainer.classList.remove('grid-view');
            bookContainer.classList.add('list-view');
            listViewBtn.classList.add('active');
            gridViewBtn.classList.remove('active');
            localStorage.setItem('bookViewPreference', 'list');
        });
        
        // Load saved preference
        const savedView = localStorage.getItem('bookViewPreference');
        if (savedView === 'list') {
            listViewBtn.click();
        } else {
            gridViewBtn.click();
        }
    }
    
    // Book detail tabs
    const bookDetailTabs = document.querySelectorAll('#book-detail-tabs .nav-link');
    if (bookDetailTabs.length > 0) {
        bookDetailTabs.forEach(tab => {
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                
                // Hide all tab contents
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('show', 'active');
                });
                
                // Show the target tab content
                document.querySelector(targetId).classList.add('show', 'active');
                
                // Update active tab
                bookDetailTabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    // Image preview for file uploads
    var imageUpload = document.getElementById('id_profile_picture');
    if (imageUpload) {
        imageUpload.addEventListener('change', function() {
            var file = this.files[0];
            if (file) {
                var reader = new FileReader();
                var preview = document.getElementById('image-preview');
                
                reader.onload = function(e) {
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.id = 'image-preview';
                        preview.className = 'img-thumbnail mt-2';
                        preview.style.maxHeight = '200px';
                        imageUpload.parentNode.insertBefore(preview, imageUpload.nextSibling);
                    }
                    preview.src = e.target.result;
                };
                
                reader.readAsDataURL(file);
            }
        });
    }

    // Password strength meter
    var password1 = document.getElementById('id_password1');
    var password2 = document.getElementById('id_password2');
    var passwordStrength = document.getElementById('password-strength');
    
    if (password1 && passwordStrength) {
        password1.addEventListener('input', function() {
            var strength = checkPasswordStrength(this.value);
            updatePasswordStrengthMeter(strength);
        });
    }
    
    if (password1 && password2) {
        password2.addEventListener('input', function() {
            if (password1.value !== this.value) {
                this.setCustomValidity('Hasła nie są identyczne.');
            } else {
                this.setCustomValidity('');
            }
        });
    }
});

/**
 * Check the strength of a password
 * @param {string} password - The password to check
 * @returns {number} A score from 0 to 4 indicating password strength
 */
function checkPasswordStrength(password) {
    let score = 0;
    
    // Length check
    if (password.length >= 8) score++;
    
    // Contains both lower and uppercase characters
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) score++;
    
    // Contains numbers
    if (password.match(/\d/)) score++;
    
    // Contains special characters
    if (password.match(/[^a-zA-Z0-9]/)) score++;
    
    return score;
}

/**
 * Update the password strength meter UI
 * @param {number} strength - The password strength score (0-4)
 */
function updatePasswordStrengthMeter(strength) {
    const strengthMeter = document.getElementById('password-strength');
    if (!strengthMeter) return;
    
    const strengthText = ['Bardzo słabe', 'Słabe', 'Średnie', 'Dobre', 'Bardzo dobre'];
    const strengthClass = ['danger', 'warning', 'info', 'success', 'success'];
    
    strengthMeter.textContent = strengthText[strength];
    strengthMeter.className = `text-${strengthClass[strength]}`;
    
    // Update progress bar if it exists
    const progressBar = document.getElementById('password-strength-bar');
    if (progressBar) {
        const width = (strength / 4) * 100;
        progressBar.style.width = `${width}%`;
        progressBar.className = `progress-bar bg-${strengthClass[strength]}`;
        progressBar.setAttribute('aria-valuenow', width);
    }
}

/**
 * Format phone number as user types
 * @param {HTMLInputElement} input - The input element
 */
function formatPhoneNumber(input) {
    // Remove all non-digit characters
    let phone = input.value.replace(/\D/g, '');
    
    // Format as (XXX) XXX-XXXX
    if (phone.length > 0) {
        phone = phone.match(/(\d{0,3})(\d{0,3})(\d{0,3})/);
        phone = !phone[2] ? phone[1] : `(${phone[1]}) ${phone[2]}` + (phone[3] ? `-${phone[3]}` : '');
    }
    
    input.value = phone;
}

// Make functions available globally
window.formatPhoneNumber = formatPhoneNumber;
