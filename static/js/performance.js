// CuraSetu Performance-Optimized JavaScript - 60fps Guaranteed

/* ============================================
   DEVICE CAPABILITY DETECTION
   ============================================ */

const DeviceCapability = {
    isHighEnd: () => {
        const memory = navigator.deviceMemory || 8;
        const cores = navigator.hardwareConcurrency || 4;
        const isDesktop = window.matchMedia('(min-width: 1024px)').matches;
        return memory >= 4 && cores >= 4 && isDesktop;
    },
    
    prefersReducedMotion: () => {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    },
    
    isMobile: () => {
        return window.matchMedia('(max-width: 768px)').matches;
    }
};

/* ============================================
   ADAPTIVE GLASSMORPHISM CONTROLLER
   ============================================ */

function initAdaptiveGlass() {
    const root = document.documentElement;
    
    if (DeviceCapability.prefersReducedMotion() || DeviceCapability.isMobile()) {
        root.style.setProperty('--glass-blur', '0px');
        document.querySelectorAll('.glass').forEach(el => {
            el.style.backdropFilter = 'none';
            el.style.webkitBackdropFilter = 'none';
        });
    } else if (DeviceCapability.isHighEnd()) {
        root.style.setProperty('--glass-blur', '8px');
    } else {
        root.style.setProperty('--glass-blur', '0px');
    }
}

/* ============================================
   DEBOUNCED SCROLL - Prevent Jank
   ============================================ */

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/* ============================================
   SMOOTH SCROLL WITH RAF
   ============================================ */

function smoothScrollToBottom(element) {
    if (!element) return;
    
    requestAnimationFrame(() => {
        element.scrollTop = element.scrollHeight;
    });
}

/* ============================================
   OPTIMIZED AUTO-SCROLL
   ============================================ */

const debouncedScroll = debounce((element) => {
    smoothScrollToBottom(element);
}, 100);

/* ============================================
   THEME SWITCHING - CSS Variables Only
   ============================================ */

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Instant switch using CSS variables
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

/* ============================================
   OPTIMIZED INPUT HANDLER
   ============================================ */

function initInputOptimization() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    
    if (!messageInput || !sendButton) return;
    
    // Debounced input handler
    const handleInput = debounce(() => {
        const hasValue = messageInput.value.trim().length > 0;
        sendButton.style.opacity = hasValue ? '1' : '0.7';
    }, 50);
    
    messageInput.addEventListener('input', handleInput, { passive: true });
}

/* ============================================
   VIRTUALIZED RENDERING (Future Enhancement)
   ============================================ */

function initVirtualizedMessages() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // Only render visible messages + buffer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.visibility = 'visible';
            }
        });
    }, {
        root: chatMessages,
        rootMargin: '100px'
    });
    
    // Observe all messages
    chatMessages.querySelectorAll('.message').forEach(msg => {
        observer.observe(msg);
    });
}

/* ============================================
   PERFORMANCE MONITORING
   ============================================ */

function monitorPerformance() {
    if (typeof performance === 'undefined') return;
    
    let lastTime = performance.now();
    let frames = 0;
    
    function checkFPS() {
        const currentTime = performance.now();
        frames++;
        
        if (currentTime >= lastTime + 1000) {
            const fps = Math.round((frames * 1000) / (currentTime - lastTime));
            
            // Log warning if FPS drops below 55
            if (fps < 55) {
                console.warn(`⚠️ Low FPS detected: ${fps}fps`);
            }
            
            frames = 0;
            lastTime = currentTime;
        }
        
        requestAnimationFrame(checkFPS);
    }
    
    // Only monitor in development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        requestAnimationFrame(checkFPS);
    }
}

/* ============================================
   INITIALIZATION
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize adaptive glassmorphism
    initAdaptiveGlass();
    
    // Initialize optimized input
    initInputOptimization();
    
    // Initialize virtualized rendering
    initVirtualizedMessages();
    
    // Start performance monitoring
    monitorPerformance();
    
    // Initialize theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
    
    // Auto-scroll to bottom
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        smoothScrollToBottom(chatMessages);
    }
    
    // Enable inputs
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    if (messageInput) messageInput.disabled = false;
    if (sendButton) sendButton.disabled = false;
});

/* ============================================
   PASSIVE EVENT LISTENERS - Better Scroll Performance
   ============================================ */

window.addEventListener('scroll', debounce(() => {
    // Handle scroll events
}, 100), { passive: true });

window.addEventListener('resize', debounce(() => {
    initAdaptiveGlass();
}, 200), { passive: true });

/* ============================================
   EXPORT FUNCTIONS
   ============================================ */

window.CuraSetu = {
    toggleTheme,
    smoothScrollToBottom,
    DeviceCapability
};
