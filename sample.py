"""sample_data.py を使って献立最適化を実行するサンプルスクリプト。"""
from __future__ import annotations
from itertools import combinations

from problem import Problem


# 栄養素リストとマッピング
NUTRIENTS = ["cal", "protein", "fat", "carbohydrates"]
NUTRIENT_NAMES = {
    0: "cal",
    1: "protein",
    2: "fat",
    3: "carbohydrates",
}
NUTRIENT_TO_ID = {name: idx for idx, name in NUTRIENT_NAMES.items()}

# 1日あたりの基準目標値
# 単位: cal(kcal), protein(g), fat(g), carbohydrates(g)
DAILY_TARGET_TEMPLATE = {
    NUTRIENT_TO_ID["cal"]: 2000,
    NUTRIENT_TO_ID["protein"]: 97.5,
    NUTRIENT_TO_ID["fat"]: 66.7,
    NUTRIENT_TO_ID["carbohydrates"]: 250.0,
}

# ペナルティ重み
ALPHA_P = {k: 1.0 for k in DAILY_TARGET_TEMPLATE}
ALPHA_M = {k: 1.0 for k in DAILY_TARGET_TEMPLATE}

# 料理リスト
# duration: 許容頻度の期間（食数）
# freq    : period 内での許容出現回数
DISHES: list[dict] = [
    # ---- 主食（丼・麺・ご飯もの） -------------------------------
    {"dish": "ごはん",           "category": "主食", "cal": 244.1, "protein":  4.2, "fat":  0.5, "carbohydrates":  55.7, "duration": 1,  "freq": 1},
    {"dish": "ごはん(小)",       "category": "主食", "cal": 168, "protein":  2.9, "fat":  0.35, "carbohydrates":  38.4, "duration": 1,  "freq": 1},
    {"dish": "ごはん(大)",       "category": "主食", "cal": 420.0, "protein":  7.2, "fat":  0.7, "carbohydrates":  95.8, "duration": 1,  "freq": 1},
    {"dish": "パン",             "category": "主食", "cal": 263.6, "protein":  9.3, "fat":  4.4, "carbohydrates":  46.7, "duration": 3,  "freq": 1},
    {"dish": "カレーライス",      "category": "主食", "cal": 666.0, "protein": 17.0, "fat": 22.0, "carbohydrates": 100.0, "duration": 21,  "freq": 1},
    {"dish": "ハヤシライス",      "category": "主食", "cal": 636.0, "protein": 16.0, "fat": 20.0, "carbohydrates":  98.0, "duration": 21,  "freq": 1},
    {"dish": "チキンカレー",      "category": "主食", "cal": 667.0, "protein": 26.0, "fat": 19.0, "carbohydrates":  98.0, "duration": 21,  "freq": 1},
    {"dish": "親子丼",            "category": "主食", "cal": 592.0, "protein": 30.0, "fat": 16.0, "carbohydrates":  82.0, "duration": 12,  "freq": 1},
    {"dish": "牛丼",              "category": "主食", "cal": 656.0, "protein": 24.0, "fat": 20.0, "carbohydrates":  95.0, "duration": 12,  "freq": 1},
    {"dish": "チャーシュー丼",    "category": "主食", "cal": 618.0, "protein": 26.0, "fat": 18.0, "carbohydrates":  88.0, "duration": 12,  "freq": 1},
    {"dish": "オムライス",        "category": "主食", "cal": 556.0, "protein": 18.0, "fat": 20.0, "carbohydrates":  76.0, "duration": 12,  "freq": 1},
    {"dish": "チャーハン",        "category": "主食", "cal": 498.0, "protein": 16.0, "fat": 18.0, "carbohydrates":  68.0, "duration": 12,  "freq": 1},
    {"dish": "ラーメン",          "category": "主食", "cal": 497.0, "protein": 20.0, "fat": 17.0, "carbohydrates":  66.0, "duration": 21,  "freq": 1},
    {"dish": "うどん",            "category": "主食", "cal": 363.0, "protein": 12.0, "fat":  3.0, "carbohydrates":  72.0, "duration": 12,  "freq": 1},
    {"dish": "そば",              "category": "主食", "cal": 334.0, "protein": 14.0, "fat":  2.0, "carbohydrates":  65.0, "duration": 12,  "freq": 1},
    # ---- 主菜（肉・魚） ----------------------------------------
    {"dish": "唐揚げ",            "category": "主菜", "cal": 354.0, "protein": 24.0, "fat": 22.0, "carbohydrates":  15.0, "duration": 21,  "freq": 1},
    {"dish": "豚の生姜焼き",      "category": "主菜", "cal": 298.0, "protein": 22.0, "fat": 18.0, "carbohydrates":  12.0, "duration": 6,  "freq": 1},
    {"dish": "とんかつ",          "category": "主菜", "cal": 434.0, "protein": 28.0, "fat": 26.0, "carbohydrates":  22.0, "duration": 21,  "freq": 1},
    {"dish": "ハンバーグ",        "category": "主菜", "cal": 376.0, "protein": 22.0, "fat": 24.0, "carbohydrates":  18.0, "duration": 21,  "freq": 1},
    {"dish": "鮭の塩焼き",        "category": "主菜", "cal": 173.2, "protein": 25.0, "fat":  8.0, "carbohydrates":   0.3, "duration": 3,  "freq": 1},
    {"dish": "さばの味噌煮",      "category": "主菜", "cal": 220.0, "protein": 20.0, "fat": 12.0, "carbohydrates":   8.0, "duration": 3,  "freq": 1},
    {"dish": "ぶりの照り焼き",    "category": "主菜", "cal": 232.0, "protein": 23.0, "fat": 12.0, "carbohydrates":   8.0, "duration": 3,  "freq": 1},
    {"dish": "天ぷら",            "category": "主菜", "cal": 322.0, "protein": 12.0, "fat": 18.0, "carbohydrates":  28.0, "duration": 6,  "freq": 1},
    {"dish": "餃子",              "category": "主菜", "cal": 294.0, "protein": 16.0, "fat": 14.0, "carbohydrates":  26.0, "duration": 12,  "freq": 1},
    {"dish": "回鍋肉",            "category": "主菜", "cal": 344.0, "protein": 18.0, "fat": 24.0, "carbohydrates":  14.0, "duration": 6,  "freq": 1},
    {"dish": "青椒肉絲",          "category": "主菜", "cal": 308.0, "protein": 20.0, "fat": 20.0, "carbohydrates":  12.0, "duration": 21,  "freq": 1},
    {"dish": "麻婆豆腐",          "category": "主菜", "cal": 290.0, "protein": 16.0, "fat": 18.0, "carbohydrates":  16.0, "duration": 12,  "freq": 1},
    # ---- 副菜・汁物 --------------------------------------------
    {"dish": "肉じゃが",          "category": "副菜", "cal": 223.0, "protein": 12.0, "fat":  7.0, "carbohydrates":  28.0, "duration": 12,  "freq": 1},
    {"dish": "ほうれん草のおひたし","category": "副菜", "cal":  41.0, "protein":  3.0, "fat":  1.0, "carbohydrates":   5.0, "duration": 3,  "freq": 1},
    {"dish": "納豆",              "category": "副菜", "cal": 100.2, "protein":  8.3, "fat":  5.0, "carbohydrates":   5.4, "duration": 3,  "freq": 1},
    {"dish": "冷奴",              "category": "副菜", "cal":  76.0, "protein":  8.0, "fat":  4.0, "carbohydrates":   2.0, "duration": 3,  "freq": 1},
    {"dish": "卵焼き",            "category": "副菜", "cal": 154.0, "protein": 10.0, "fat": 10.0, "carbohydrates":   6.0, "duration": 3,  "freq": 1},
    {"dish": "味噌汁",            "category": "副菜", "cal":  36.8, "protein":  2.5, "fat":  1.2, "carbohydrates":   4.0, "duration": 3,  "freq": 1},
    {"dish": "豚汁",              "category": "副菜", "cal": 121.0, "protein":  7.0, "fat":  5.0, "carbohydrates":  12.0, "duration": 3,  "freq": 1},
    {"dish": "サラダ",            "category": "副菜", "cal":  58.0, "protein":  2.0, "fat":  2.0, "carbohydrates":   8.0, "duration": 3,  "freq": 1},
]

# 排他ペア（同一食事への同時割り当て不可）
# 同系統の料理・似た主食は同じ食事に出さない
EXCLUSIVE_PAIRS: list[list[str]] = [
    ["鮭の塩焼き",    "さばの味噌煮"],     # 焼き魚同士
    ["鮭の塩焼き",    "ぶりの照り焼き"],   # 焼き魚同士
    ["さばの味噌煮",  "ぶりの照り焼き"],   # 魚の煮物・照り焼き
    ["鮭の塩焼き",    "餃子"],            # 焼き魚と中華
    ["鮭の塩焼き",    "回鍋肉"],          # 焼き魚と中華
    ["鮭の塩焼き",    "青椒肉絲"],        # 焼き魚と中華
    ["鮭の塩焼き",    "麻婆豆腐"],        # 焼き魚と中華
    ["さばの味噌煮",  "餃子"],            # 魚の煮物と中華
    ["さばの味噌煮",  "回鍋肉"],          # 魚の煮物と中華
    ["さばの味噌煮",  "青椒肉絲"],        # 魚の煮物と中華
    ["さばの味噌煮",  "麻婆豆腐"],        # 魚の煮物と中華
    ["ぶりの照り焼き", "餃子"],           # 魚の照り焼きと中華
    ["ぶりの照り焼き", "回鍋肉"],         # 魚の照り焼きと中華
    ["ぶりの照り焼き", "青椒肉絲"],        # 魚の照り焼きと中華
    ["ぶりの照り焼き", "麻婆豆腐"],        # 魚の照り焼きと中華
    ["鮭の塩焼き",    "カレーライス"],     # 焼き魚とカレーライス
    ["さばの味噌煮",  "カレーライス"],     # 魚の煮物とカレーライス
    ["ぶりの照り焼き", "カレーライス"],     # 魚の照り焼きとカレーライス
    ["鮭の塩焼き",    "ハヤシライス"],     # 焼き魚とハヤシライス
    ["さばの味噌煮",  "ハヤシライス"],     # 魚の煮物とハヤシライス
    ["ぶりの照り焼き", "ハヤシライス"],     # 魚の照り焼きとハヤシライス
    ["鮭の塩焼き",    "チキンカレー"],     # 焼き魚とチキンカレー
    ["さばの味噌煮",  "チキンカレー"],     # 魚の煮物とチキンカレー
    ["ぶりの照り焼き", "チキンカレー"],     # 魚の照り焼きとチキンカレー
    ["回鍋肉",       "青椒肉絲"],         # 中華炒め同士（豚肉ベース）
    ["回鍋肉",       "麻婆豆腐"],         # 中華おかず重複
    ["味噌汁",       "豚汁"],             # 汁物同士
    ["パン",         "唐揚げ"],           # パンは中華との組み合わせを避ける
    ["パン",         "餃子"],             # パンは中華との組み合わせを避ける
    ["パン",         "回鍋肉"],           # パンは中華との組み合わせを避ける
    ["パン",         "青椒肉絲"],         # パンは中華との組み合わせを避ける
    ["パン",         "麻婆豆腐"],         # パンは中華との組み合わせを避ける
    ["パン",         "とんかつ"],         # パンは和食との組み合わせを避ける
    ["パン",         "鮭の塩焼き"],       # パンは和食との組み合わせを避ける
    ["パン",         "さばの味噌煮"],     # パンは和食との組み合わせを避ける
    ["パン",         "ぶりの照り焼き"],   # パンは和食との組み合わせを避ける
    ["パン",         "納豆"],            # パンは和食との組み合わせを避ける
    ["パン",         "冷奴"],            # パンは和食との組み合わせを避ける
    ["パン",         "味噌汁"],          # パンは和食との組み合わせを避ける
    ["パン",         "豚汁"],            # パンは和食との組み合わせを避ける
    ["そば",         "餃子"],            # そばは中華との組み合わせを避ける
    ["そば",         "回鍋肉"],          # そばは中華との組み合わせを避ける
    ["そば",         "青椒肉絲"],        # そばは中華との組み合わせを避ける
    ["そば",         "麻婆豆腐"],        # そばは中華との組み合わせを避ける
    ["うどん",       "餃子"],            # うどんは中華との組み合わせを避ける
    ["うどん",       "回鍋肉"],          # うどんは中華との組み合わせを避ける
    ["うどん",       "青椒肉絲"],        # うどんは中華との組み合わせを避ける
    ["うどん",       "麻婆豆腐"],        # うどんは中華との組み合わせを避ける
]

# 主食カテゴリ同士は同一食事に割り当てない（既存ペアは重複追加しない）
_staple_dishes = [dish["dish"] for dish in DISHES if dish["category"] == "主食"]
_exclusive_pair_set = {frozenset(pair) for pair in EXCLUSIVE_PAIRS}
for left, right in combinations(_staple_dishes, 2):
    pair_set = frozenset((left, right))
    if pair_set not in _exclusive_pair_set:
        EXCLUSIVE_PAIRS.append([left, right])
        _exclusive_pair_set.add(pair_set)

# 過去の食事履歴（最適化開始前の1週間 = 21食分）
# インデックス順: [朝食, 昼食, 夕食] × 7日
# 排他ペアの組み合わせは同一エントリーに含めない
INITIAL_PAST_MEAL: list[list[str]] = [
    # Day 1
    ["ごはん", "卵焼き", "味噌汁"],                   # 朝
    ["そば", "天ぷら"],                               # 昼
    ["鮭の塩焼き", "肉じゃが", "味噌汁"],             # 夕
    # Day 2
    ["パン", "卵焼き", "サラダ"],                     # 朝
    ["カレーライス", "サラダ"],                        # 昼
    ["唐揚げ", "ほうれん草のおひたし", "豚汁"],       # 夕
    # Day 3
    ["ごはん", "サラダ", "味噌汁"],                   # 朝
    ["うどん"],                                       # 昼
    ["ハンバーグ", "サラダ", "味噌汁"],               # 夕
    # Day 4
    ["パン", "卵焼き", "サラダ"],                     # 朝
    ["チャーハン"],                                    # 昼
    ["さばの味噌煮", "ほうれん草のおひたし", "豚汁"],  # 夕
    # Day 5
    ["ごはん", "サラダ", "味噌汁"],                   # 朝
    ["親子丼"],                                       # 昼
    ["豚の生姜焼き", "冷奴", "味噌汁"],               # 夕
    # Day 6
    ["パン", "サラダ"],                               # 朝
    ["ラーメン"],                                     # 昼
    ["回鍋肉", "ほうれん草のおひたし", "味噌汁"],     # 夕
    # Day 7
    ["ごはん", "サラダ", "味噌汁"],                   # 朝
    ["牛丼"],                                         # 昼
    ["麻婆豆腐", "卵焼き", "豚汁"],                   # 夕
]


def build_problem(
        past_meal: list[list[str]],
        optimize_days: int = 1,
        min_dishes: int = 2,
        time_limit: float = 10.0
    ) -> Problem:
    """Problem インスタンスへ変換する。

    Args:
        past_meal: 過去の食事履歴。[[朝食の料理名のリスト], [昼食の料理名のリスト], [夕食の料理名のリスト]], ...] の形式で、最適化開始前の食事を日ごとにまとめたリスト
        optimize_days: 最適化する日数
        min_dishes: 1回の食事に含める最低料理数
        time_limit: ソルバーのタイムリミット（秒）
    """
    N = {
        day: DAILY_TARGET_TEMPLATE.copy()
        for day in range(optimize_days)
    }

    dish_names: dict[int, str] = {}
    dish_name_to_id: dict[str, int] = {}
    A: dict[int, dict[int, float]] = {}
    D: dict[int, int] = {}
    F: dict[int, int] = {}

    for dish_id, dish in enumerate(DISHES):
        dish_name = dish["dish"]
        dish_names[dish_id] = dish_name
        dish_name_to_id[dish_name] = dish_id

        A[dish_id] = {
            NUTRIENT_TO_ID[nut]: float(dish[nut])
            for nut in NUTRIENTS
        }
        D[dish_id] = int(dish["duration"])
        F[dish_id] = int(dish["freq"])

    C: list[tuple[int, int]] = []
    for left_name, right_name in EXCLUSIVE_PAIRS:
        left_id = dish_name_to_id[left_name]
        right_id = dish_name_to_id[right_name]
        C.append((left_id, right_id))

    M = len(past_meal)  # 過去の食事数
    past_meals: dict[int, list[int]] = {}
    for meal_idx, dishes_in_meal in enumerate(past_meal):
        past_meals[meal_idx] = [dish_name_to_id[name] for name in dishes_in_meal]

    return Problem(
        M=M,
        L=optimize_days,
        N=N,
        A=A,
        D=D,
        F=F,
        P=min_dishes,
        C=C,
        alpha_p=ALPHA_P,
        alpha_m=ALPHA_M,
        dish_names=dish_names,
        nutrient_names=NUTRIENT_NAMES,
        past_meals=past_meals,
        time_limit=time_limit,
    )
