/**
 * MOONSTONE Support Email - Anti-Bot Display
 *
 * Displays support email in an obfuscated way to prevent bot harvesting.
 * Reveals on hover/click.
 *
 * Usage:
 *   <span data-support-email></span>
 *   <script src="/static/js/support-email.js"></script>
 */

(function() {
    'use strict';

    // Encoded email parts (simple obfuscation)
    const _p1 = 'aW5mbw==';  // info
    const _p2 = 'd2ViM3Bob3RvLmNvbQ==';  // web3photo.com
    const _at = '@';

    function decode(str) {
        try {
            return atob(str);
        } catch {
            return '';
        }
    }

    function getEmail() {
        return decode(_p1) + _at + decode(_p2);
    }

    // Inject styles
    const style = document.createElement('style');
    style.textContent = `
        .moonstone-email {
            display: inline-block;
            cursor: pointer;
            color: var(--gold, #d4a574);
            border-bottom: 1px dotted currentColor;
            transition: all 0.3s ease;
            position: relative;
        }

        .moonstone-email:hover {
            color: var(--cyan, #5aa8b9);
        }

        .moonstone-email .email-hidden {
            display: none;
        }

        .moonstone-email .email-mask {
            opacity: 0.7;
        }

        .moonstone-email.revealed .email-hidden {
            display: inline;
        }

        .moonstone-email.revealed .email-mask {
            display: none;
        }

        .moonstone-email::before {
            content: "◈ ";
            opacity: 0.5;
        }

        .moonstone-email:not(.revealed)::after {
            content: " ↗";
            font-size: 0.7em;
            opacity: 0.5;
            vertical-align: super;
        }
    `;
    document.head.appendChild(style);

    // Initialize all support email elements
    function init() {
        const elements = document.querySelectorAll('[data-support-email]');

        elements.forEach(el => {
            if (el.classList.contains('moonstone-email-initialized')) return;

            el.classList.add('moonstone-email');
            el.classList.add('moonstone-email-initialized');

            // Create masked version
            const mask = document.createElement('span');
            mask.className = 'email-mask';
            mask.textContent = 'support [at] web3···';

            // Create revealed version
            const hidden = document.createElement('span');
            hidden.className = 'email-hidden';

            // Build email with mailto link
            const email = getEmail();
            const link = document.createElement('a');
            link.href = 'mailto:' + email + '?subject=[MOONSTONE-HELP] Support Request';
            link.textContent = email;
            link.style.color = 'inherit';
            link.style.textDecoration = 'none';
            hidden.appendChild(link);

            el.appendChild(mask);
            el.appendChild(hidden);

            // Reveal on hover
            el.addEventListener('mouseenter', () => {
                el.classList.add('revealed');
            });

            // Optional: Hide on leave (comment out to keep revealed)
            // el.addEventListener('mouseleave', () => {
            //     el.classList.remove('revealed');
            // });

            // Set title for accessibility
            el.title = 'Hover to reveal support email';
        });
    }

    // Auto-init on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export for manual use
    window.MoonstoneSupport = {
        init: init,
        getEmail: getEmail
    };
})();
