document.addEventListener('DOMContentLoaded', () => {
    if (typeof completedGoals === 'undefined' || completedGoals.length === 0) return;

    const seenKey = 'vaultly_seen_goals';
    const seen = JSON.parse(localStorage.getItem(seenKey) || '[]');

    for (const goal of completedGoals) {
        if (!seen.includes(goal.name)) {
            const modal = new bootstrap.Modal(document.getElementById('goal-popup'));
            document.getElementById('goal-popup-title').textContent = `${goal.name} Achieved!`;
            document.getElementById('goal-popup-body').textContent  =
                `You hit your $${goal.amount} target. Incredible work — time to set the next one!`;
            modal.show();
            seen.push(goal.name);
            localStorage.setItem(seenKey, JSON.stringify(seen));
            break;
        }
    }
});


function animateValue(el, start, end, duration, prefix, suffix) {
    if (!el) return;
    const range     = end - start;
    const startTime = performance.now();

    function step(now) {
        const elapsed  = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased    = 1 - Math.pow(1 - progress, 3);
        const current  = Math.round(start + range * eased);
        el.textContent = prefix + current.toLocaleString() + suffix;
        if (progress < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
}

function animateNumber(el, start, end, duration, decimals = 0, prefix = '', suffix = '') {
    if (!el) return;
    const range = end - start;
    const startTime = performance.now();
    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = start + range * eased;
        const absVal = Math.abs(current);
        const formatted = absVal.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
         const sign = current < 0 ? '−' : '';
        el.textContent = (sign || '') + prefix + formatted + suffix;
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function animateCurrency(el, start, end, duration) {
    if (!el) return;
    const range = end - start;
    const startTime = performance.now();
    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = start + range * eased;
        const sign = current >= 0 ? '+' : '−';
        const absVal = Math.round(Math.abs(current));
        el.textContent = sign + '$' + absVal.toLocaleString();
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function animateSignedCurrency(el, start, end, duration, decimals = 2) {
    if (!el) return;
    const range = end - start;
    const startTime = performance.now();
    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = start + range * eased;
        const sign = current >= 0 ? '+' : '−';
        const absVal = Math.abs(current);
        const formatted = absVal.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
        el.textContent = sign + '$' + formatted;
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function animateSignedPercent(el, start, end, duration, decimals = 2) {
    if (!el) return;
    const range = end - start;
    const startTime = performance.now();
    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = start + range * eased;
        const sign = current >= 0 ? '+' : '−';
        const absVal = Math.abs(current);
        const formatted = absVal.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
        el.textContent = sign + formatted + '%';
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.kpi-value').forEach(el => {
        const text = el.textContent.trim();
        if (/[a-zA-Z]/.test(text)) return;
        const prefixMatch = text.match(/^([^\d]*)/);
        const suffixMatch = text.match(/([^\d]*)$/);
        const prefix = prefixMatch ? prefixMatch[1] : '';
        const suffix = suffixMatch ? suffixMatch[1] : '';
        const cleaned = text.replace(/[^\d.]/g, '');
        const end = parseFloat(cleaned);
        if (!isNaN(end) && end !== 0) animateValue(el, 0, end, 900, prefix, suffix);
    });
});


document.addEventListener('DOMContentLoaded', () => {
     const bars = document.querySelectorAll('.goal-progress-fill, .budget-bar-fill, .cat-bar-fill');
     bars.forEach(bar => {
         const target    = bar.style.width;
         bar.style.width = '0%';
         setTimeout(() => { bar.style.width = target; }, 300);
    });
});


(function () {
    const path = window.location.pathname;
    document.querySelectorAll('.sidebar-nav-item a').forEach(link => {
        if (link.getAttribute('href') === path) {
            link.closest('.sidebar-nav-item').classList.add('active');
        } else {
            link.closest('.sidebar-nav-item').classList.remove('active');
        }
    });
})();
