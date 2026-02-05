# backend/context_processors.py
from .settings import GlobalJSONEncoder

def json_encoder(request):
    return {
        'JSON_ENCODER': GlobalJSONEncoder,
        'json_encoder': GlobalJSONEncoder
    }