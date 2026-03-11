const cards = document.querySelectorAll('.feature-card');
let lastActive = document.getElementById('card-vault');

cards.forEach(card => {
    card.addEventListener('mouseenter', () => {
        cards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        lastActive = card;
    });
});