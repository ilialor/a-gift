/**
 * Менеджер аутентификации для Telegram WebApp
 */
// Remove 'const' to define AuthManager in the global scope
AuthManager = {
  botUsername: null, 

  /**
   * Сохранить параметры аутентификации при первой загрузке
   */
  saveParams() {
      const urlParams = new URLSearchParams(window.location.search);
      const authData = {
          startParam: urlParams.get('startParam') || window.Telegram.WebApp.initDataUnsafe?.query_id,
          refresh_token: urlParams.get('refresh_token'),
          initData: window.Telegram?.WebApp?.initData
      };

      if (authData.startParam && authData.refresh_token) {
          localStorage.setItem('authData', JSON.stringify(authData));
          console.log('Auth parameters saved');
      }
  },

  /**
   * Получить сохраненные параметры аутентификации
   */
  getParams() {
      const authData = localStorage.getItem('authData');
      return authData ? JSON.parse(authData) : null;
  },

  /**
   * Добавить параметры аутентификации к URL
   */
  addParamsToUrl(url) {
      const authData = this.getParams();
      if (!authData) return url;

      const urlObj = new URL(url, window.location.origin);
      urlObj.searchParams.set('startParam', authData.startParam);
      urlObj.searchParams.set('refresh_token', authData.refresh_token);
      if (authData.initData) {
          urlObj.searchParams.set('initData', authData.initData);
      }
      return urlObj.toString();
  },

  /**
   * Добавить параметры аутентификации к заголовкам запроса
   */
  addAuthHeaders() {
      const authData = this.getParams();
      if (!authData) return {};

      return {
          'X-Start-Param': authData.startParam,
          'X-Refresh-Token': authData.refresh_token,
          'X-Init-Data': authData.initData || ''
      };
  },

  /**
   * Обработать все ссылки на странице
   */
  handleLinks() {
      document.querySelectorAll('a').forEach(link => {
          if (link.href.startsWith(window.location.origin + '/twa/')) {
              link.href = this.addParamsToUrl(link.href);
          }
      });
  },

  /**
   * Обработать ответ с новым токеном
   */
  handleTokenRefresh(response) {
      const newToken = response.headers.get('X-New-Access-Token');
      if (newToken) {
          const authData = this.getParams();
          if (authData) {
              authData.startParam = newToken;
              localStorage.setItem('authData', JSON.stringify(authData));
              console.log('Token refreshed');
          }
      }
  },

  /**
   * Выполнить запрос с авторизацией
   */
  async fetchWithAuth(url, options = {}) {
      const authData = this.getParams();
      if (!authData) {
          console.error('No auth data available');
          throw new Error('Authentication required');
      }

      const headers = {
          ...options.headers,
          'X-Start-Param': authData.startParam,
          'X-Refresh-Token': authData.refresh_token,
          'X-Init-Data': authData.initData || ''
      };

      try {
          const response = await fetch(url, { ...options, headers });

          // Handle token refresh
          const newAccessToken = response.headers.get('X-New-Access-Token');
          if (newAccessToken) {
              authData.startParam = newAccessToken;
              localStorage.setItem('authData', JSON.stringify(authData));
              console.log('Access token refreshed');
          }

          if (!response.ok) {
              // Логируем детали запроса при ошибке
              console.error('Auth request failed:', {
                  status: response.status,
                  statusText: response.statusText,
                  headers: Object.fromEntries(response.headers.entries()),
                  authHeaders: headers
              });

              if (response.status === 401) {
                  // Очищаем текущие данные авторизации
                  localStorage.removeItem('authData');
                  // Используем сохраненное имя бота
                  if (this.botUsername) {
                      window.location.href = `https://t.me/${this.botUsername}`;
                  } else {
                      // Если имя бота не установлено, делаем запрос к API
                      try {
                          const botInfoResponse = await fetch('/twa/api/bot-info');
                          const botInfo = await botInfoResponse.json();
                          window.location.href = `https://t.me/${botInfo.username}`;
                      } catch (e) {
                          console.error('Failed to get bot username:', e);
                          throw new Error('Authentication required. Please return to the bot.');
                      }
                  }
                  throw new Error('Session expired. Please reauthorize through the bot.');
              }
              throw new Error(response.statusText || 'Request failed');
          }

          return response;
      } catch (error) {
          console.error('Fetch error:', error);
          throw error;
      }
  },

  /**
   * Инициализировать менеджер аутентификации
   */
  init() {
      if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
          window.Telegram.WebApp.ready();
          window.Telegram.WebApp.setHeaderColor('secondary_bg_color');
          window.Telegram.WebApp.setBackgroundColor('secondary_bg_color');
          
          if (window.Telegram.WebApp.BackButton) {
              window.Telegram.WebApp.BackButton.show();
          }
          
          window.Telegram.WebApp.expand();

          // Проверяем наличие return_url в параметрах
          const urlParams = new URLSearchParams(window.location.search);
          const returnTo = urlParams.get('return_to');
          if (returnTo) {
              // Редиректим на сохраненный URL
              window.location.href = decodeURIComponent(returnTo);
              return;
          }
      }

      this.saveParams();
      this.handleLinks();
      console.log('AuthManager initialized', {
          isWebApp: typeof window !== 'undefined' ? !!window.Telegram?.WebApp : false,
          platform: typeof window !== 'undefined' ? window.Telegram?.WebApp?.platform || 'web' : 'server',
          botUsername: this.botUsername
      });
  },

  setBotUsername(username) {
      this.botUsername = username;
      console.log('Bot username set:', username);
  },

  isWebAppEnvironment() {
      return !!(window.Telegram?.WebApp?.initData);
  },

  /**
   * Прямая авторизация через WebApp
   */
  async directAuth() {
      try {
          // Log environment info for debugging
          console.log('WebApp environment check:', {
              isWebApp: !!(window.Telegram?.WebApp),
              initDataExists: !!(window.Telegram?.WebApp?.initData)
          });

          // Проверяем наличие WebApp и initData
          if (!window.Telegram?.WebApp?.initData) {
              throw new Error('No Telegram WebApp data available');
          }

          const response = await fetch('/twa/api/auth/direct', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                  init_data: window.Telegram.WebApp.initData,
                  return_url: window.location.pathname + window.location.search
              })
          });

          if (!response.ok) {
              const data = await response.json();
              throw new Error(data.detail || 'Authentication failed');
          }

          const data = await response.json();
          const authData = {
              startParam: data.access_token,
              refresh_token: data.refresh_token,
              initData: window.Telegram.WebApp.initData
          };
          
          localStorage.setItem('authData', JSON.stringify(authData));
          return data;
      } catch (error) {
          console.error('Direct auth error:', error);
          throw error;
      }
  }
};

// Ensure AuthManager is attached to the window object
window.AuthManager = AuthManager;

// Export для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AuthManager;
}

// Автоматическая инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  AuthManager.init();
});
