pip freeze > requirements.txt


'requirements.txt' contains at minimum:


django>=4.2
djangorestframework>=3.14
django-cors-headers>=4.0
python-socketio>=5.10
python-dotenv>=1.0
openai>=1.0
PyJWT>=2.8
social-auth-app-django>=5.4
djangorestframework-simplejwt>=5.3
Pillow>=10.0
uvicorn>=0.24
aiohttp>=3.9
asgiref>=3.7
google-auth>=2.23
google-auth-oauthlib>=1.1



dalia-backend/
│
├── dalia/                      # Project config
│   ├── settings.py             # All configuration
│   ├── urls.py                 # Root URL routing
│   └── asgi.py                 # Socket.IO + Django mounted here
│
├── core/                       # Shared utilities
│   └── responses.py            # DaliaResponse unified structure
│
├── users/                      # Auth domain
│   ├── models.py               # Custom User model
│   ├── serializers.py          # Register, Login, Google, Me
│   ├── views.py                # Auth endpoints
│   ├── urls.py                 # /api/auth/
│   └── admin.py
│
├── conversations/              # Chat domain
│   ├── models.py               # Conversation, Message,
│   │                           # ExecutionSession, ExecutionStep
│   ├── serializers.py          # Full nested serializers
│   ├── views.py                # CRUD + message history
│   ├── urls.py                 # /api/conversations/
│   └── admin.py
│
├── integrations/               # Connected tools domain
│   ├── models.py               # Integration, IntegrationPermission
│   ├── serializers.py          # Connect, permissions
│   ├── views.py                # App Manager endpoints
│   ├── urls.py                 # /api/integrations/
│   └── admin.py
│
├── agent/                      # AI execution domain
│   ├── socket_server.py        # Socket.IO server, all WS events
│   ├── orchestrator.py         # Execution lifecycle manager
│   ├── intent_parser.py        # OpenAI intent parsing
│   ├── executors.py            # Action executors
│   └── __init__.py
│
├── manage.py
├── requirements.txt
├── .env
└── db.sqlite3




## Complete API Reference

Here is every endpoint Flutter will call:

AUTH
POST   /api/auth/register/          -> Register with email
POST   /api/auth/login/             -> Login with email
POST   /api/auth/google/            -> Login with Google
GET    /api/auth/me/                -> Get logged in user

CONVERSATIONS
GET    /api/conversations/                        -> List all conversations
POST   /api/conversations/                        -> Create conversation
GET    /api/conversations/<id>/                   -> Get conversation + messages
PATCH  /api/conversations/<id>/                   -> Update title
DELETE /api/conversations/<id>/                   -> Delete conversation
GET    /api/conversations/<id>/messages/          -> Paginated messages
DELETE /api/conversations/<id>/clear/             -> Clear messages
GET    /api/conversations/sessions/<id>/          -> Execution session detail

INTEGRATIONS
GET    /api/integrations/                         -> All tools list
POST   /api/integrations/connect/                 -> Connect a tool
GET    /api/integrations/<tool>/                  -> Tool detail
DELETE /api/integrations/<tool>/disconnect/       -> Disconnect tool
PATCH  /api/integrations/<tool>/permissions/      -> Toggle permission

WEBSOCKET EVENTS (Socket.IO)
emit   send_instruction    -> Send user instruction
emit   retry_step          -> Retry a failed step
emit   ping                → Keep connection alive

listen connected           -> Connection confirmed
listen instruction_received -> Backend acknowledged
listen parsing_intent      -> OpenAI is working
listen plan_ready          -> Execution plan built
listen step_started        -> A step is now running
listen step_completed      -> A step finished successfully
listen step_failed         -> A step failed with error
listen execution_complete  -> Full execution done
listen pong                -> Ping response




