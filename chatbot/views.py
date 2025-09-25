from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import ChatThread, ChatMessage
from .services import GeminiService

@login_required
def chat_view(request):
    threads = ChatThread.objects.filter(user=request.user)
    active_thread = threads.first() if threads.exists() else None
    return render(request, 'chatbot/chat.html', {
        'threads': threads,
        'active_thread': active_thread
    })

@login_required
def new_thread(request):
    thread = ChatThread.objects.create(user=request.user)
    return redirect('chatbot:thread', thread_id=thread.id)

@login_required
def thread_view(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
    threads = ChatThread.objects.filter(user=request.user)
    messages = thread.messages.all()
    return render(request, 'chatbot/chat.html', {
        'threads': threads,
        'active_thread': thread,
        'messages': messages
    })

@csrf_exempt
@login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message')
        thread_id = data.get('thread_id')
        
        if not thread_id:
            thread = ChatThread.objects.create(user=request.user, title=user_message[:50])
        else:
            thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
        
        # Get AI response
        gemini_service = GeminiService()
        bot_response = gemini_service.get_health_advice(user_message)
        
        # Save message
        chat_message = ChatMessage.objects.create(
            thread=thread,
            user_message=user_message,
            bot_response=bot_response
        )
        
        # Update thread timestamp
        thread.save()
        
        return JsonResponse({
            'success': True,
            'bot_response': bot_response,
            'thread_id': thread.id,
            'message_id': chat_message.id
        })
    
    return JsonResponse({'success': False})