import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .utils import (
    AGE_CHOICES,
    ACTIVITY_CHOICES,
    calculate_der,
)


def calculator_view(request):
    """渲染計算器頁面"""
    context = {
        'age_choices': AGE_CHOICES,
        'activity_choices': ACTIVITY_CHOICES,
    }
    return render(request, 'nutrition/calculator.html', context)


@require_POST
def calculate_api(request):
    """POST API：計算每日營養需求，回傳 JSON"""
    try:
        data = json.loads(request.body)
        weight_kg = float(data.get('weight', 0))
        age_category = data.get('age_category', '')
        activity_level = data.get('activity_level', '')

        if weight_kg <= 0:
            return JsonResponse({'error': '請輸入有效的體重（大於 0）'}, status=400)

        result = calculate_der(weight_kg, age_category, activity_level)
        return JsonResponse({'success': True, **result})

    except (ValueError, TypeError) as e:
        return JsonResponse({'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': '無效的請求格式'}, status=400)
