"""献立を作成するサンプル問題インスタンスを作成し、最適化結果を表示する実行可能モジュール."""
from solver import Solver
from problem import Problem
from solution import Solution

from sample import (
    INITIAL_PAST_MEAL,
    build_problem
)

def main() -> None:
    """サンプル最適化の実行エントリポイント。"""
    past_meal = INITIAL_PAST_MEAL.copy()
    for day in range(1, 8):
        print(f"Day {day}")

        # 問題インスタンスを作成
        problem: Problem = build_problem(
            past_meal=past_meal,
            optimize_days=1,
            min_dishes=2,
            time_limit=20.0
        )

        # 最適化実行
        solver: Solver = Solver(problem)
        solution: Solution = solver.solve()

        # 献立と栄養価を表示
        meal_labels = ["朝食", "昼食", "夕食"]

        problem = solution.problem
        menus = solution.menus
        nutritions = solution.nutritions
        for day in range(problem.L):
            for p in range(3):
                meal_idx = day * 3 + p
                dish_names = menus[meal_idx] if meal_idx < len(menus) else []
                dish_text = ", ".join(dish_names) if dish_names else "(なし)"
                print(f"  {meal_labels[p]}: {dish_text}")

            day_nutritions = nutritions[day] if day < len(nutritions) else {}
            for nutrient_id, nutrient_name in problem.nutrient_names.items():
                total = day_nutritions.get(nutrient_name, 0.0)
                target = problem.N[day][nutrient_id]
                deviation = (total - target) / target * 100
                print(f"  {nutrient_name}: {total:.1f} / {target:.1f} ({deviation:.1f}%)")

        past_meal.extend(solution.menus)


if __name__ == "__main__":
    main()
