document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des datepickers
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        // S'assurer que la date minimale est aujourd'hui pour les nouveaux trajets
        if (input.getAttribute('name') === 'departure_date') {
            const today = new Date().toISOString().split('T')[0];
            input.setAttribute('min', today);
        }
    });

    // Gestion des formulaires de confirmation (suppression, etc.)
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const message = form.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Validation du formulaire de réservation
    const reservationForm = document.querySelector('form.reservation-form');
    if (reservationForm) {
        reservationForm.addEventListener('submit', function(e) {
            const seatsInput = this.querySelector('input[name="seats"]');
            const availableSeats = parseInt(seatsInput.getAttribute('data-max-seats'));
            const requestedSeats = parseInt(seatsInput.value);

            if (requestedSeats > availableSeats) {
                e.preventDefault();
                alert(`Désolé, il n'y a que ${availableSeats} place(s) disponible(s).`);
            }
        });
    }

    // Animation des messages flash
    const messages = document.querySelectorAll('.messages .alert');
    messages.forEach(message => {
        // Faire disparaître les messages après 5 secondes
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease-in-out';
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });

    // Gestion des filtres de recherche
    const searchForm = document.querySelector('form.search-form');
    if (searchForm) {
        const clearFilters = document.createElement('button');
        clearFilters.type = 'button';
        clearFilters.className = 'btn btn-link';
        clearFilters.textContent = 'Effacer les filtres';
        clearFilters.addEventListener('click', function() {
            const inputs = searchForm.querySelectorAll('input');
            inputs.forEach(input => input.value = '');
            searchForm.submit();
        });

        const formActions = document.createElement('div');
        formActions.className = 'text-right mt-2';
        formActions.appendChild(clearFilters);
        searchForm.appendChild(formActions);
    }

    // Amélioration de l'expérience utilisateur pour les demandes de réservation
    const requestButtons = document.querySelectorAll('.request-action-btn');
    requestButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const action = this.getAttribute('data-action');
            const requestId = this.getAttribute('data-request-id');
            
            // Désactiver tous les boutons du même groupe
            const siblingButtons = this.closest('.request-actions').querySelectorAll('button');
            siblingButtons.forEach(btn => btn.disabled = true);
            
            // Ajouter une classe de chargement
            this.classList.add('loading');
        });
    });

    // Gestion des onglets avec conservation de l'état
    const tabLinks = document.querySelectorAll('.nav-tabs .nav-link');
    tabLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Sauvegarder l'onglet actif dans le localStorage
            localStorage.setItem('activeRideTab', this.getAttribute('href'));
        });
    });

    // Restaurer l'onglet actif au chargement
    const activeTab = localStorage.getItem('activeRideTab');
    if (activeTab) {
        const tab = document.querySelector(`a[href="${activeTab}"]`);
        if (tab) {
            tab.click();
        }
    }
}); 