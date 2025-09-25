from django.urls import path
from .views import chat_view, new_thread, thread_view, send_message

app_name = 'chatbot'

urlpatterns = [
    path('', chat_view, name='chat'),
    path('new/', new_thread, name='new_thread'),
    path('thread/<int:thread_id>/', thread_view, name='thread'),
    path('send/', send_message, name='send_message'),
]