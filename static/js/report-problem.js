// Handle report problem form submission
document.addEventListener('DOMContentLoaded', function() {
    // Find the submit button for any type of error report
    const submitProblemBtn = document.getElementById('submitProblemReport') || 
                            document.getElementById('submitAuthorErrorReport') || 
                            document.getElementById('submitPublisherErrorReport');
    
    if (submitProblemBtn) {
        submitProblemBtn.addEventListener('click', function() {
            // Determine which type of form we're dealing with
            let problemType, problemDescription, modalId, formId;
            
            if (document.getElementById('problemType')) {
                // Book error report
                problemType = document.getElementById('problemType').value;
                problemDescription = document.getElementById('problemDescription').value;
                modalId = 'reportProblemModal';
                formId = 'reportProblemForm';
            } else if (document.getElementById('authorErrorType')) {
                // Author error report
                problemType = document.getElementById('authorErrorType').value;
                problemDescription = document.getElementById('authorErrorDescription').value;
                modalId = 'reportAuthorErrorModal';
                formId = 'reportAuthorErrorForm';
            } else if (document.getElementById('publisherErrorType')) {
                // Publisher error report
                problemType = document.getElementById('publisherErrorType').value;
                problemDescription = document.getElementById('publisherErrorDescription').value;
                modalId = 'reportPublisherErrorModal';
                formId = 'reportPublisherErrorForm';
            }
            
            // Form validation
            if (!problemType || !problemDescription) {
                alert('Proszę wypełnić wszystkie wymagane pola.');
                return;
            }
            
            // Here you would normally send the data to the server
            // For now, we'll just show a success message and close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
            modal.hide();
            
            // Show success message
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show';
            alertDiv.setAttribute('role', 'alert');
            alertDiv.innerHTML = `
                <strong>Dziękujemy!</strong> Twoje zgłoszenie zostało przyjęte i zostanie rozpatrzone.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            // Insert the alert at the top of the main content
            const mainContent = document.querySelector('.container.py-4');
            mainContent.insertBefore(alertDiv, mainContent.firstChild);
            
            // Reset form
            document.getElementById(formId).reset();
        });
    }
});
