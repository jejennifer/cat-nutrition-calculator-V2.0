import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .utils import (
    AGE_CHOICES,
    ACTIVITY_CHOICES,
    calculate_der,
    load_dry_food_data,
)


def calculator_view(request):
    """渲染計算器頁面"""
    dry_foods = list(load_dry_food_data())

    context = {
        'age_choices': AGE_CHOICES,
        'activity_choices': ACTIVITY_CHOICES,
        'dry_foods': dry_foods,
        'dry_foods_json': json.dumps(dry_foods, ensure_ascii=False),
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
        dry_food_kcal_per_kg = int(data.get('dry_food_kcal_per_kg', 0))
        dry_food_g = float(data.get('dry_food_g', 0))

        if weight_kg <= 0:
            return JsonResponse({'error': '請輸入有效的體重（大於 0）'}, status=400)

        result = calculate_der(
            weight_kg, age_category, activity_level,
            dry_food_kcal_per_kg, dry_food_g,
        )
        return JsonResponse({'success': True, **result})

    except (ValueError, TypeError) as e:
        return JsonResponse({'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': '無效的請求格式'}, status=400)
