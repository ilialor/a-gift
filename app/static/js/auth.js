/**
 * Менеджер аутентификации для Telegram WebApp
 */
const AuthManager = {
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
      const headers = {
          ...options.headers,
          ...this.addAuthHeaders()
      };

      const response = await fetch(url, { ...options, headers });
      this.handleTokenRefresh(response);
      return response;
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
      }

      this.saveParams();
      this.handleLinks();
      console.log('AuthManager initialized', {
          isWebApp: typeof window !== 'undefined' ? !!window.Telegram?.WebApp : false,
          platform: typeof window !== 'undefined' ? window.Telegram?.WebApp?.platform || 'web' : 'server'
      });
  }
};

// Export для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AuthManager;
}

// Автоматическая инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  AuthManager.init();
});
