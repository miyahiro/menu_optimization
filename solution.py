"""献立の最適化の問題の結果を格納するモジュール."""
from __future__ import annotations
from typing import TYPE_CHECKING

import pulp

if TYPE_CHECKING:
    from problem import Problem


class Solution:
    """献立の最適化の問題の結果を格納するクラス."""

    def __init__(
        self,
        menus: dict[int, list[int]],
        nutritions: dict[int, dict[int, float]],
        problem: Problem,
        lp_problem: pulp.LpProblem,
    ) -> None:
        """Solutionクラスのコンストラクタ。

        Args:
            menus: 食事番号（0始まり）-> 割り当てられた料理IDのリスト。
                   食事番号 j は最適化対象期間の先頭を 0 とした連番。
            nutritions: 日番号（0始まり）-> {栄養素ID: 1日合計摂取量}。
            problem: 元の問題インスタンスへの参照。
            lp_problem: PuLPの数理計画問題インスタンスへの参照。
        """
        self.problem = problem
        self.lp_problem = lp_problem

        # 外部公開は料理名・栄養素名ベースにする
        meal_size = max(menus.keys(), default=-1) + 1
        self._menus: list[list[str]] = []
        for meal_idx in range(meal_size):
            dish_ids = menus.get(meal_idx, [])
            self._menus.append([problem.dish_names[dish_id] for dish_id in dish_ids])

        day_size = max(nutritions.keys(), default=-1) + 1
        self._nutritions: list[dict[str, float]] = []
        for day_idx in range(day_size):
            day_nutrition_by_id = nutritions.get(day_idx, {})
            self._nutritions.append(
                {
                    problem.nutrient_names[nutrient_id]: value
                    for nutrient_id, value in day_nutrition_by_id.items()
                }
            )

    @property
    def menus(self) -> list[list[str]]:
        """献立のリストを返す.

        Returns:
            list[list[str]]: 食事番号（0始まり）順の献立リスト。
                各要素は、その食事に割り当てられた料理名のリスト。
        """
        return self._menus

    @property
    def nutritions(self) -> list[dict[str, float]]:
        """栄養素の1日合計摂取量を返す.

        Returns:
            list[dict[str, float]]: 日番号（0始まり）順の栄養素マップ。
                各要素のキーは栄養素名、値はその栄養素の1日合計摂取量。
        """
        return self._nutritions

