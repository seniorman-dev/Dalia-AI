import asyncio

import socketio
import jwt
import json
from django.conf import settings
from django.contrib.auth import get_user_model





# Create async Socket.IO server
# cors_allowed_origins allows Flutter client to connect from any origin

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True,        # add this to see more detail in logs
    transports=['websocket', 'polling'],  # allow polling fallback
    ping_timeout=60,
    ping_interval=25,
)

User = get_user_model()



async def get_user_from_token(token: str):
    """
    Basically, my Flutter frontend sends it's JWT when connecting.
    We decode it here to identify who is connecting.
    Returns the user object or None if invalid.
    """
    try:
        # Decode the JWT
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        # SimpleJWT stores user id in 'user_id' field
        user_id = payload.get('user_id')
        if not user_id:
            return None

        # Fetch the user from DB
        user = await asyncio.to_thread(
            User.objects.get, id=user_id
        )
        return user
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except User.DoesNotExist:
        return None



@sio.event
async def connect(sid, environ: dict, auth: dict):
    print(f"[SOCKET] Connection attempt: {sid}")
    
    # Fall back to HTTP header (Postman testing)
    if not auth or 'token' not in auth:
        # Postman sends it as an HTTP header
        raw = environ.get('HTTP_AUTH', '')
        if raw:
            import json
            try:
                auth = json.loads(raw)
            except Exception:
                auth = {}

    if not auth or 'token' not in auth:
        print(f"[SOCKET] No auth token. Rejecting {sid}")
        return False

    token = auth['token'].replace('Bearer ', '')
    user = await get_user_from_token(token)

    if not user:
        print(f"[SOCKET] Invalid token. Rejecting {sid}")
        return False

    # This lets us know who this socket belongs to
    await sio.save_session(sid, {
        'user_id': str(user.id),
        'user_email': user.email,
        'full_name': user.full_name
    })

    # This lets us send targeted events to specific users
    await sio.enter_room(sid, str(user.id))

    print(f"[SOCKET] Connected: {user.email} (sid: {sid})")

    await sio.emit('connected', {
        'message': f'Welcome back, {user.full_name}',
        'user_id': str(user.id)
    }, to=sid)



@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    email = session.get('user_email', 'unknown') if session else 'unknown'
    print(f"[SOCKET] Disconnected: {email} (sid: {sid})")



@sio.event
async def send_instruction(sid, data: dict):

    import asyncio
    from agent.orchestrator import AgentOrchestrator

    session = await sio.get_session(sid)
    if not session:
        await sio.emit('error', {
            'message': 'Unauthorized'
        }, to=sid)
        return

    user_id = session['user_id']
    instruction = data.get('instruction', '').strip()
    conversation_id = data.get('conversation_id')

    if not instruction:
        await sio.emit('execution_error', {
            'message': 'No instruction provided'
        }, to=sid)
        return

    print(f"[SOCKET] Instruction from {session['user_email']}: {instruction[:60]}...")

    await sio.emit('instruction_received', {
        'message': 'Got it. Working on it now...',
        'instruction': instruction
    }, to=sid)

    # The orchestrator handles everything else and
    # streams events back through the socket
    orchestrator = AgentOrchestrator(
        sio=sio,
        sid=sid,
        user_id=user_id,
        conversation_id=conversation_id
    )

    # Run orchestration in background
    # so the socket stays free for other events
    asyncio.create_task(
        orchestrator.execute(instruction)
    )


@sio.event
async def retry_step(sid, data: dict):

    from agent.orchestrator import AgentOrchestrator

    session = await sio.get_session(sid)
    if not session:
        return

    session_id = data.get('session_id')
    step_id = data.get('step_id')

    orchestrator = AgentOrchestrator(
        sio=sio,
        sid=sid,
        user_id=session['user_id'],
        conversation_id=None
    )

    import asyncio
    asyncio.create_task(
        orchestrator.retry_step(session_id, step_id)
    )


@sio.event
async def ping(sid, data):
    await sio.emit('pong', {'status': 'alive'}, to=sid)