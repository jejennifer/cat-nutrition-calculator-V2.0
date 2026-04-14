"""
貓咪每日營養需求計算模組

公式：
  RER (靜態能量需求) = 70 × 體重(kg)^0.75
  DER (每日能量需求) = RER × 年齡係數 × 活動係數
  剩餘鮮食熱量 = DER - (乾糧克數 / 1000 × 該乾糧 kcal/kg)
  鮮食營養素 = 所需營養素 - 乾糧營養素
"""

import csv
import os
from functools import lru_cache
from pathlib import Path

# 取得專案的 BASE_DIR (目前檔案在 src/nutrition/utils.py)
BASE_DIR = Path(__file__).resolve().parent.parent

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


def _parse_percent(s: str) -> float:
    """將 '34.40%' 或 '34%' 轉為小數 0.344"""
    s = s.strip().replace('%', '')
    try:
        return float(s) / 100
    except (ValueError, TypeError):
        return 0.0


@lru_cache(maxsize=1)
def load_dry_food_data() -> tuple:
    """
    從 CSV 讀取乾糧資料並回傳 tuple[dict]（使用 lru_cache 避免每次請求重讀檔案）。
    CSV 結構: 食物名稱,類型,水分,蛋白質,脂肪,碳水,熱量
    現在也包含各營養素百分比，供前端計算乾糧提供的營養素克數。
    """
    csv_path = os.path.join(BASE_DIR, 'nutrition', 'ref', 'food_data_dry_20260122.csv')

    dry_foods = []

    if not os.path.exists(csv_path):
        return tuple(dry_foods)

    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('食物名稱', '').strip()
            kcal_str = row.get('熱量', '').strip()

            # 從 "4025cal/1kg" 中擷取數字 "4025"
            kcal_per_kg = 0
            if kcal_str:
                digits = ''.join(filter(str.isdigit, kcal_str.split('cal')[0]))
                if digits:
                    kcal_per_kg = int(digits)

            # 解析營養素百分比
            protein_pct = _parse_percent(row.get('蛋白質', '0'))
            fat_pct = _parse_percent(row.get('脂肪', '0'))
            carb_pct = _parse_percent(row.get('碳水', '0'))

            if name and kcal_per_kg > 0:
                dry_foods.append({
                    'name': name,
                    'kcal_per_kg': kcal_per_kg,
                    'protein_pct': round(protein_pct, 4),
                    'fat_pct': round(fat_pct, 4),
                    'carb_pct': round(carb_pct, 4),
                })

    return tuple(dry_foods)


def calculate_rer(weight_kg: float) -> float:
    """計算靜態能量需求 (RER) = 70 × weight^0.75"""
    if weight_kg <= 0:
        raise ValueError('體重必須大於 0')
    return 70 * (weight_kg ** 0.75)


def calculate_der(
    weight_kg: float,
    age_category: str,
    activity_level: str,
    dry_food_kcal_per_kg: int = 0,
    dry_food_g: float = 0,
    dry_food_protein_pct: float = 0,
    dry_food_fat_pct: float = 0,
    dry_food_carb_pct: float = 0,
) -> dict:
    """
    計算每日能量需求 (DER) 以及營養素建議量。
    若提供乾糧資料，將計算乾糧營養素及剩餘鮮食需要補足的營養素。

    回傳 dict:
      - rer, der, age_factor, activity_factor
      - protein_g, fat_g, carb_g: 每日建議總營養素 (g)
      - dry_food_kcal: 乾糧提供的熱量 (kcal)
      - remaining_kcal: 剩餘需要鮮食補足的熱量 (kcal)
      - dry_protein_g, dry_fat_g, dry_carb_g: 乾糧提供的營養素 (g)
      - fresh_protein_g, fresh_fat_g, fresh_carb_g: 鮮食需補足的營養素 (g)
    """
    if age_category not in AGE_FACTORS:
        raise ValueError(f'無效的年齡層: {age_category}')
    if activity_level not in ACTIVITY_FACTORS:
        raise ValueError(f'無效的活動量: {activity_level}')

    age_factor = AGE_FACTORS[age_category]
    activity_factor = ACTIVITY_FACTORS[activity_level]

    rer = calculate_rer(weight_kg)
    der = rer * age_factor * activity_factor

    # 乾糧熱量扣除
    dry_food_kcal = (dry_food_g / 1000) * dry_food_kcal_per_kg
    remaining_kcal = max(0, der - dry_food_kcal)

    # 每日建議總營養素
    # 蛋白質: 約 52% 熱量 → 1g 蛋白質 = 4 kcal
    # 脂肪:   約 36% 熱量 → 1g 脂肪 = 9 kcal
    # 碳水:   約 12% 熱量 → 1g 碳水 = 4 kcal
    protein_g = (der * 0.52) / 4
    fat_g = (der * 0.36) / 9
    carb_g = (der * 0.12) / 4

    # 乾糧提供的營養素（克數 = 餵食克數 × 營養素百分比）
    dry_protein_g = dry_food_g * dry_food_protein_pct
    dry_fat_g = dry_food_g * dry_food_fat_pct
    dry_carb_g = dry_food_g * dry_food_carb_pct

    # 鮮食需補足的營養素 = 總需求 - 乾糧提供（不低於 0）
    fresh_protein_g = max(0, protein_g - dry_protein_g)
    fresh_fat_g = max(0, fat_g - dry_fat_g)
    fresh_carb_g = max(0, carb_g - dry_carb_g)

    return {
        'rer': round(rer, 1),
        'der': round(der, 1),
        'age_factor': age_factor,
        'activity_factor': activity_factor,
        'protein_g': round(protein_g, 1),
        'fat_g': round(fat_g, 1),
        'carb_g': round(carb_g, 1),
        'dry_food_kcal': round(dry_food_kcal, 1),
        'remaining_kcal': round(remaining_kcal, 1),
        'dry_protein_g': round(dry_protein_g, 1),
        'dry_fat_g': round(dry_fat_g, 1),
        'dry_carb_g': round(dry_carb_g, 1),
        'fresh_protein_g': round(fresh_protein_g, 1),
        'fresh_fat_g': round(fresh_fat_g, 1),
        'fresh_carb_g': round(fresh_carb_g, 1),
    }
