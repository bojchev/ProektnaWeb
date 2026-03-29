


function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    sidebar.classList.toggle('collapsed');
    const collapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('sidebarExpanded', !collapsed);
    swapLogo(collapsed);
}

function swapLogo(collapsed) {
    const logo      = document.getElementById('sidebar-logo');
    const logoSmall = document.getElementById('sidebar-logo-small');
    if (!logo || !logoSmall) return;
    logo.style.display      = collapsed ? 'none' : '';
    logoSmall.style.display = collapsed ? ''     : 'none';
}


(function () {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    const saved = localStorage.getItem('sidebarExpanded');
    if (saved === 'false') {
        sidebar.classList.add('collapsed');
        swapLogo(true);
    }
})();


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
    const bars = document.querySelectorAll('.goal-progress-fill, .budget-bar-fill');
    bars.forEach(bar => {
        const target    = bar.style.width;
        bar.style.width = '0';
        setTimeout(() => { bar.style.width = target; }, 200);
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
