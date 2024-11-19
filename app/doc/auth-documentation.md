# Telegram WebApp Authentication System Documentation

## Overview

This authentication system is designed for Telegram Mini Apps (TWA), providing seamless user experience while maintaining security through JWT tokens and Telegram's built-in authentication mechanisms.

## Authentication Flow

1. **Initial Authentication (Bot Side)**

   - User starts the bot (/start command)
   - Bot creates/retrieves user record in database
   - Bot generates JWT `access_token` and `refresh_token` with `user_id`
   - Bot provides WebApp button with tokens in `startParam`

2. **WebApp Authentication Flow**

   - TWA receives `initData` from Telegram
   - TWA receives `startParam` with `access_token`
   - Middleware validates both parameters
   - User gains access to protected routes

3. **Token Refresh Flow**

   - When `access_token` is about to expire or has expired, TWA automatically sends `refresh_token` to `/auth/refresh`
   - Server validates `refresh_token` and issues new `access_token` and `refresh_token`
   - Tokens are updated in the client’s `localStorage`

4. **Navigation Authentication**

   - Auth parameters stored in `localStorage` on first load
   - Parameters automatically added to internal navigation
   - Seamless authentication maintained between pages

## Data Structures

### User Database Fields

```python
class User:
    id: int  # Primary Key
    username: str  # Telegram username
    telegram_id: int  # Telegram user ID
    email: str  # Optional
    password: str  # Generated from token
```

### JWT Token Structure

```json
{
  "user_id": 123456,
  "created": 1679825645,
  "exp": 1679827445 // 30 minutes from creation
}
```

### LocalStorage Data

```json
{
  "tgAuthData": {
    "initData": "query_id=...",
    "startParam": "jwt_token_here"
  }
}
```

## Implementation Details

### 1. Bot Handler (Initial Authentication)

```python
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    # Create/get user
    user = await get_or_create_user(message.from_user)

    # Generate JWT token
    token = auth_manager.create_token(user.id)

    # Create WebApp button
    webapp_url = f"{settings.webapp_url}?tgWebAppStartParam={token}"
    webapp_btn = create_webapp_button(webapp_url)

    await message.answer("Welcome!", reply_markup=webapp_btn)
```

### 2. Authentication Middleware

```python
class TelegramWebAppMiddleware:
    async def dispatch(request: Request):
        # Get auth parameters
        init_data = request.query_params.get('initData')
        start_param = request.query_params.get('tgWebAppStartParam')

        # Validate parameters
        validate_telegram_data(init_data)
        user_id = validate_jwt_token(start_param)

        # Set user context
        request.state.user_id = user_id
```

### 3. Client-Side Authentication Preservation

```javascript
const AuthManager = {
  // Save on first load
  saveParams() {
    const params = new URLSearchParams(window.location.search);
    const authData = {
      initData: params.get("initData"),
      startParam: params.get("tgWebAppStartParam"),
    };
    if (authData.initData && authData.startParam) {
      localStorage.setItem("tgAuthData", JSON.stringify(authData));
    }
  },

  // Add to navigation
  addParamsToUrl(url) {
    const authData = JSON.parse(localStorage.getItem("tgAuthData"));
    const newUrl = new URL(url);

    if (authData) {
      newUrl.searchParams.set("initData", authData.initData);
      newUrl.searchParams.set("tgWebAppStartParam", authData.startParam);
    }

    return newUrl.toString();
  },
};
```

## Security Considerations

1. **JWT Token Security**

   - Short lifetime (30 minutes)
   - Contains only essential data
   - Signed with secure secret

2. **Telegram Validation**

   - Validates initData hash
   - Confirms user identity
   - Prevents direct URL access

3. **Client-Side Security**
   - localStorage used only for auth params
   - Parameters validated on every request
   - No sensitive data stored

## Error Handling

1. **Invalid Token**

   ```http
   Status: 401 Unauthorized
   Response: Error page with return to bot option
   ```

2. **Missing Parameters**

   ```http
   Status: 401 Unauthorized
   Response: "This page can only be accessed through Telegram"
   ```

3. **Expired Token**
   ```http
   Status: 401 Unauthorized
   Response: "Session expired, please return to bot"
   ```

## Navigation Examples

1. **Direct Bot Link**

   ```
   https://your-domain.com/twa/?initData=...&tgWebAppStartParam=...
   ```

2. **Internal Navigation**

   ```javascript
   // Original URL
   /twa/gifts

   // Transformed URL
   /twa/gifts?initData=...&tgWebAppStartParam=...
   ```

## Testing Authentication

1. **Bot Integration Test**

   ```python
   async def test_bot_start():
       response = await bot.send_message(user_id, "/start")
       assert "Welcome" in response.text
       assert response.reply_markup  # Contains WebApp button
   ```

2. **WebApp Authentication Test**
   ```python
   async def test_webapp_auth():
       token = create_test_token()
       response = await client.get(f"/twa/?initData=test&startParam={token}")
       assert response.status_code == 200
   ```

## Best Practices

1. Always validate both initData and startParam
2. Keep JWT tokens short-lived
3. Implement proper error handling
4. Use secure token storage
5. Validate user identity on each request

## Design

1. Token Refresh Flow
   sequenceDiagram
    participant Frontend
    participant AuthManager
    participant Router
    participant DAO

    Frontend->>Router: Sends /auth/refresh with refresh_token
    Router->>AuthManager: Validate refresh_token
    AuthManager-->>Router: user_id
    Router->>DAO: Find User by ID
    DAO-->>Router: User Object
    Router->>AuthManager: Create new access and refresh tokens
    Router->>DAO: Update Refresh Token
    Router-->>Frontend: New tokens

    [Token Refresh Flow](SD1.png)

2. Handling Unauthorized Access
   sequenceDiagram
    participant User
    participant Frontend
    participant Middleware
    participant Router

    User->>Frontend: Requests /twa/gifts without tokens
    Frontend->>Middleware: Sends Request without auth parameters
    Middleware->>Router: Detect missing auth
    Router-->>Middleware: Redirect to /twa/error
    Middleware->>Frontend: RedirectResponse to /twa/error?message=Authentication+error
    Frontend-->>User: Displays Error Page

[Handling Unauthorized Access](SD3.png)

3. User Registration via Bot
   sequenceDiagram
    participant User
    participant TelegramBot
    participant Router
    participant DAO
    participant AuthManager

    User->>TelegramBot: Sends /start command
    TelegramBot->>Router: Triggers cmd_start handler in `app/bot/handlers/router.py`
    Router->>DAO: Check if user exists
    DAO-->>Router: User not found
    Router->>DAO: Create new user
    DAO-->>Router: User object
    Router->>AuthManager: Create access and refresh tokens
    AuthManager-->>Router: Tokens
    Router->>DAO: Update refresh_token
    DAO-->>Router: Confirmation
    Router->>TelegramBot: Send Welcome message with WebApp button
    TelegramBot-->>User: Receives Welcome message

[User Registration via Bot](SD2.png)
