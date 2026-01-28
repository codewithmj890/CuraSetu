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
    try:
        thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
    except:
        return redirect('chatbot:chat')
    
    threads = ChatThread.objects.filter(user=request.user)
    messages = thread.messages.all()
    return render(request, 'chatbot/chat.html', {
        'threads': threads,
        'active_thread': thread,
        'messages': messages
    })

@login_required
def delete_thread(request, thread_id):
    if request.method == 'POST':
        thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
        thread.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def toggle_pin(request, thread_id):
    if request.method == 'POST':
        thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
        thread.is_pinned = not thread.is_pinned
        thread.save()
        return JsonResponse({'success': True, 'is_pinned': thread.is_pinned})
    return JsonResponse({'success': False})

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
        
        # Auto-rename thread from first message
        if thread.title == "New Chat" and thread.messages.count() == 1:
            # Extract meaningful title from first message
            title = user_message[:50].strip()
            # If title ends mid-word, truncate to last complete word
            if len(user_message) > 50 and ' ' in title:
                title = title.rsplit(' ', 1)[0] + '...'
            thread.title = title
            thread.save()
        
        # Update thread timestamp
        thread.save()
        
        return JsonResponse({
            'success': True,
            'bot_response': bot_response,
            'thread_id': thread.id,
            'message_id': chat_message.id
        })
    
    return JsonResponse({'success': False})