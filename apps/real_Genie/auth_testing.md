# Auth Testing Playbook (Emergent Google Auth)

This file is referenced by the testing agent to validate the Emergent Google Auth flow for the Ember app.

## Test User Setup

```bash
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'test.user.' + Date.now() + '@example.com',
  name: 'Ember Tester',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Backend API tests
```bash
# Should return user data
curl -X GET "$API_URL/api/auth/me" -H "Authorization: Bearer $TOKEN"

# Should return user-scoped conversations only
curl -X GET "$API_URL/api/conversations" -H "Authorization: Bearer $TOKEN"

# Should create a chat under this user
curl -X POST "$API_URL/api/chat" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"message":"hello"}'
```

## Browser test
```python
await page.context.add_cookies([{
    "name": "session_token",
    "value": "YOUR_SESSION_TOKEN",
    "domain": "move-forward-112.preview.emergentagent.com",
    "path": "/",
    "httpOnly": True,
    "secure": True,
    "sameSite": "None"
}])
await page.goto("https://move-forward-112.preview.emergentagent.com/")
# Should land on chat (not login)
```

## Cleanup
```bash
mongosh --eval "
use('test_database');
db.users.deleteMany({email: /test\.user\./});
db.user_sessions.deleteMany({session_token: /test_session/});
db.conversations.deleteMany({user_id: /test-user/});
db.messages.deleteMany({user_id: /test-user/});
db.memories.deleteMany({user_id: /test-user/});
db.user_settings.deleteMany({user_id: /test-user/});
"
```

## Checklist
- [ ] User doc has `user_id` (UUID, not MongoDB `_id`)
- [ ] Session `user_id` matches user's `user_id`
- [ ] All queries use `{"_id": 0}` projection
- [ ] Conversations / messages / memories / user_settings all carry `user_id`
- [ ] `/api/auth/me` returns user data with both Bearer and Cookie auth
- [ ] Logout clears cookie and deletes session
- [ ] Two test users see only their own data (data isolation)
