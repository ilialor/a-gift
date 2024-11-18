// auth.js
const AuthManager = {
    // Key for localStorage
    STORAGE_KEY: 'tgAuthData',
    
    // Time to live for stored auth data (30 minutes in milliseconds)
    TTL: 30 * 60 * 1000,

    // Save auth parameters with timestamp
    saveParams() {
        const params = new URLSearchParams(window.location.search);
        const initData = params.get('initData');
        const startParam = params.get('tgWebAppStartParam');
        const refreshToken = params.get('refresh_token');  

        // Only save if tokens are not already saved
        const saved = localStorage.getItem(this.STORAGE_KEY);
        if (!saved && initData && startParam && refreshToken) {
            const authData = {
                initData,
                startParam,
                refreshToken,  
                timestamp: Date.now()
            };
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(authData));
            console.log('Auth parameters saved');
        }
    },

    // Get saved parameters if they haven't expired
    getParams() {
        try {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            if (!saved) return null;

            const authData = JSON.parse(saved);
            const now = Date.now();

            // Check if data has expired
            if (now - authData.timestamp > this.TTL) {
                // Redirect to error page if auth expired
                logger.error('Session expired');
                window.location.href = '/twa/error?message=Session+expired';
                return null;
            }

            // Update timestamp to extend session
            authData.timestamp = now;
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(authData));
            
            return {
                initData: authData.initData,
                startParam: authData.startParam,
                refreshToken: authData.refreshToken  // Используем сохраненный refreshToken
            };
        } catch (error) {
            console.error('Error reading auth data:', error);
            localStorage.removeItem(this.STORAGE_KEY);
            return null;
        }
    },

    // Add parameters to URL
    addParamsToUrl(url) {
        try {
            const authData = this.getParams();
            if (!authData) return url;

            const newUrl = new URL(url, window.location.origin);
            if (authData.initData) {
                newUrl.searchParams.set('initData', authData.initData);
            }
            if (authData.startParam) {
                newUrl.searchParams.set('tgWebAppStartParam', authData.startParam);
            }
            if (authData.refreshToken) {
                newUrl.searchParams.set('refresh_token', authData.refreshToken);
            }
            return newUrl.toString();
        } catch (error) {
            console.error('Error adding params to URL:', error);
            return url;
        }
    },

    // Handle internal navigation
    handleNavigation(event) {
        const link = event.target.closest('a');
        if (!link) return;

        // Only handle internal TWA links
        if (link.href.includes('/twa/')) {
            event.preventDefault();
            const newUrl = this.addParamsToUrl(link.href);
            
            // Use history.pushState for smoother navigation
            try {
                window.history.pushState({}, '', newUrl);
                // Dispatch a custom event that can be listened to for page updates
                window.dispatchEvent(new CustomEvent('twaNavigate', { 
                    detail: { url: newUrl } 
                }));
            } catch (error) {
                // Fallback to regular navigation
                window.location.href = newUrl;
            }
        }
    },

    // Handle token refresh
    async refreshToken() {
        const authData = this.getParams();
        if (authData && authData.refreshToken) {
            try {
                const response = await fetch('/auth/refresh', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ refresh_token: authData.refreshToken })
                });
                if (response.ok) {
                    const data = await response.json();
                    const newAuthData = {
                        initData: authData.initData,
                        startParam: data.access_token,
                        refreshToken: data.refresh_token,
                        timestamp: Date.now()
                    };
                    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(newAuthData));
                } else {
                    // Redirect to error page if refresh fails
                    window.location.href = '/twa/error?message=Session+expired';
                }
            } catch (error) {
                console.error("Token refresh failed:", error);
                window.location.href = '/twa/error?message=Session+expired';
            }
        }
    },

    // Initialize Telegram WebApp features
    initTelegramWebApp() {
        if (window.Telegram?.WebApp) {
            // Enable closing confirmation if needed
            window.Telegram.WebApp.enableClosingConfirmation();
            
            // Set dark/light theme
            document.documentElement.classList.toggle('dark', 
                window.Telegram.WebApp.colorScheme === 'dark'
            );
        }
    },

    // Initialize all auth manager features
    init() {
        this.saveParams();
        this.initTelegramWebApp();
        
        // Get current path
        const path = window.location.pathname;
        
        // Skip auth check for the error page
        if (path.startsWith('/twa/error')) { // Ensures all variants are excluded
            return;
        }
        
        // Ensure URL has auth params on page load only if not already redirected
        const params = new URLSearchParams(window.location.search);
        const initData = params.get('initData');
        const startParam = params.get('tgWebAppStartParam');
        
        if (!initData && !startParam) {
            const authParams = this.getParams();
            if (authParams) {
                const newUrl = new URL(window.location.href);
                if (authParams.initData) {
                    newUrl.searchParams.set('initData', authParams.initData);
                }
                if (authParams.startParam) {
                    newUrl.searchParams.set('tgWebAppStartParam', authParams.startParam);
                }
                window.history.replaceState({}, '', newUrl);
            } else {
                // Redirect to error page if auth params are missing
                window.location.href = '/twa/error?message=Session+expired';
            }
        }
        
        // Handle clicks on links
        document.removeEventListener('click', (e) => this.handleNavigation(e)); // Prevent multiple listeners
        document.addEventListener('click', (e) => this.handleNavigation(e));
        
        // Handle back/forward browser navigation
        window.addEventListener('popstate', () => {
            const newUrl = this.addParamsToUrl(window.location.href);
            if (newUrl !== window.location.href) {
                window.location.href = newUrl;
            }
        });

        // Periodically check auth status
        setInterval(() => {
            if (!this.getParams()) {
                // Redirect to error page if auth expired
                window.location.href = '/twa/error?message=Session+expired';
            }
        }, 60000); // Check every minute

        // Periodically refresh the token
        setInterval(() => {
            this.refreshToken();
        }, 5 * 60 * 1000); // Refresh every 5 minutes
    }
};
