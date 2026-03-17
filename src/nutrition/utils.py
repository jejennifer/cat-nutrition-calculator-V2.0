"""
貓咪每日營養需求計算模組

公式：
  RER (靜態能量需求) = 70 × 體重(kg)^0.75
  DER (每日能量需求) = RER × 年齡係數 × 活動係數
"""

# 年齡層係數
AGE_FACTORS = {
    'kitten_0_4': 3.0,    # 幼貓 0-4 月
    'kitten_4_6': 2.5,    # 幼貓 4-6 月
    'intact_adult': 1.4,  # 未結紮成貓
    'neutered_adult': 1.2, # 結紮成貓
    'senior': 1.1,         # 老貓
    'weight_loss': 0.8,    # 減重
}

# 活動量係數
ACTIVITY_FACTORS = {
    'low': 0.9,
    'medium': 1.0,
    'high': 1.1,
}

# 年齡層選項（用於前端顯示）
AGE_CHOICES = [
    ('kitten_0_4', '幼貓 0–4 月'),
    ('kitten_4_6', '幼貓 4–6 月'),
    ('intact_adult', '未結紮成貓'),
    ('neutered_adult', '結紮成貓'),
    ('senior', '老貓'),
    ('weight_loss', '減重'),
]

# 活動量選項（用於前端顯示）
ACTIVITY_CHOICES = [
    ('low', '低'),
    ('medium', '中'),
    ('high', '高'),
]


def calculate_rer(weight_kg: float) -> float:
    """計算靜態能量需求 (RER) = 70 × weight^0.75"""
    if weight_kg <= 0:
        raise ValueError('體重必須大於 0')
    return 70 * (weight_kg ** 0.75)


def calculate_der(weight_kg: float, age_category: str, activity_level: str) -> dict:
    """
    計算每日能量需求 (DER) 以及營養素建議量。

    回傳 dict:
      - rer: 靜態能量需求 (kcal)
      - der: 每日能量需求 (kcal)
      - age_factor: 年齡係數
      - activity_factor: 活動係數
      - protein_g: 每日蛋白質建議 (g)
      - fat_g: 每日脂肪建議 (g)
      - carb_g: 每日碳水化合物建議 (g)
    """
    if age_category not in AGE_FACTORS:
        raise ValueError(f'無效的年齡層: {age_category}')
    if activity_level not in ACTIVITY_FACTORS:
        raise ValueError(f'無效的活動量: {activity_level}')

    age_factor = AGE_FACTORS[age_category]
    activity_factor = ACTIVITY_FACTORS[activity_level]

    rer = calculate_rer(weight_kg)
    der = rer * age_factor * activity_factor

    # 營養素建議分佈
    # 蛋白質: 約 52% 熱量 → 1g 蛋白質 = 4 kcal
    # 脂肪:   約 36% 熱量 → 1g 脂肪 = 9 kcal
    # 碳水:   約 12% 熱量 → 1g 碳水 = 4 kcal
    protein_g = (der * 0.52) / 4
    fat_g = (der * 0.36) / 9
    carb_g = (der * 0.12) / 4

    return {
        'rer': round(rer, 1),
        'der': round(der, 1),
        'age_factor': age_factor,
        'activity_factor': activity_factor,
        'protein_g': round(protein_g, 1),
        'fat_g': round(fat_g, 1),
        'carb_g': round(carb_g, 1),
    }
