"""献立の最適化を行うモジュール."""
import pulp

from problem import Problem
from solution import Solution


class Solver:
    """献立の最適化を行うクラス."""

    def __init__(self, problem: Problem):
        """Solverクラスのコンストラクタ.

        Args:
            problem: 最適化対象の問題インスタンス.
        """
        self._problem = problem

    def solve(self) -> Solution:
        """問題インスタンスを受け取って、最適な献立を返す.

        Returns:
            Solution: 最適化結果

        Raises:
            RuntimeError: ソルバーが最適解を見つけられなかった場合
        """
        # 問題インスタンスから必要なデータを抽出
        prob = self._problem
        M = prob.M
        L = prob.L
        dishes = list(prob.A.keys())
        nutrients = list(prob.N[0].keys()) if L > 0 else []

        # 過去食事の定数 X_past[i][j] ∈ {0, 1}  (j ∈ 0..M-1)
        X_past: dict[int, dict[int, int]] = {}
        for i in dishes:
            X_past[i] = {}
            for j in range(M):
                dish_list = prob.past_meals.get(j, [])
                X_past[i][j] = 1 if i in dish_list else 0

        # --- PuLP モデル構築 ---
        lp = pulp.LpProblem("menu_optimization", pulp.LpMinimize)

        opt_meals = list(range(M, M + 3 * L))

        # 決定変数: X[i][j] ∈ {0, 1}
        X: dict[int, dict[int, pulp.LpVariable]] = {
            i: {
                j: pulp.LpVariable(f"x_{i}_{j}", cat="Binary")
                for j in opt_meals
            }
            for i in dishes
        }

        # 補助変数: s_plus[k][d], s_minus[k][d] >= 0
        # 栄養素キーは int ID なので変数名にそのまま使用できる
        s_plus: dict[int, dict[int, pulp.LpVariable]] = {
            k: {
                d: pulp.LpVariable(f"sp_{k}_{d}", lowBound=0)
                for d in range(L)
            }
            for k in nutrients
        }
        s_minus: dict[int, dict[int, pulp.LpVariable]] = {
            k: {
                d: pulp.LpVariable(f"sm_{k}_{d}", lowBound=0)
                for d in range(L)
            }
            for k in nutrients
        }

        # 目的関数
        lp += pulp.lpSum(
            prob.alpha_p[k] * s_plus[k][d] / prob.N[d][k]
            + prob.alpha_m[k] * s_minus[k][d] / prob.N[d][k]
            for k in nutrients
            for d in range(L)
        )

        # 制約1: 栄養素バランス制約（1日3食の合計を日単位の目標値と照合）
        for k in nutrients:
            for d in range(L):
                daily_intake = pulp.lpSum(
                    prob.A[i].get(k, 0.0) * X[i][M + 3 * d + p]
                    for i in dishes
                    for p in range(3)
                )
                lp += (
                    daily_intake == prob.N[d][k] + s_plus[k][d] - s_minus[k][d],
                    f"nutrition_{k}_{d}",
                )

        # 制約2: 許容頻度制約（スライディングウィンドウ、過去食事も考慮）
        for i in dishes:
            Di = prob.D[i]
            Fi = prob.F[i]
            for t in opt_meals:
                window_start = max(0, t - Di + 1)

                # 過去食事区間 [window_start, M-1] の定数合計
                past_count = sum(
                    X_past[i][j]
                    for j in range(window_start, M)
                )

                # 最適化対象区間 [max(M, window_start), t] の変数合計
                opt_vars = pulp.lpSum(
                    X[i][j]
                    for j in range(max(M, window_start), t + 1)
                )

                lp += (opt_vars + past_count <= Fi, f"freq_{i}_{t}")

        # 制約3: 組み合わせ制約（相性の悪い料理ペアを同一食事に割り当てない）
        for i, i_prime in prob.C:
            for j in opt_meals:
                lp += (X[i][j] + X[i_prime][j] <= 1, f"combo_{i}_{i_prime}_{j}")

        # 制約4: 最低料理数制約（1回の食事には P 個以上の料理を含める）
        for j in opt_meals:
            lp += (
                pulp.lpSum(X[i][j] for i in dishes) >= prob.P,
                f"min_dish_{j}",
            )

        # 制約5: 栄養素摂取量の範囲制約（目標値の0.8～1.2倍の範囲に収める）
        for k in nutrients:
            for d in range(L):
                daily_intake = pulp.lpSum(
                    prob.A[i].get(k, 0.0) * X[i][M + 3 * d + p]
                    for i in dishes
                    for p in range(3)
                )
                lp += (
                    daily_intake >= 0.8 * prob.N[d][k],
                    f"nutrient_lower_{k}_{d}",
                )
                lp += (
                    daily_intake <= 1.2 * prob.N[d][k],
                    f"nutrient_upper_{k}_{d}",
                )

        # --- 求解 ---
        # タイムリミット付きで求解。制限時間内に見つかった最良の解を返す
        status = lp.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=prob.time_limit))

        # ステータスと変数値の評価：
        if status == pulp.constants.LpStatusInfeasible:
            # 問題が実行不可能な場合はエラーとする
            raise RuntimeError(
                f"問題が実行不可能です。ソルバーステータス: {pulp.LpStatus[lp.status]}"
            )
        elif status == pulp.constants.LpStatusUnbounded:
            # 問題が無限に良い解を持っている場合も、実際には変数に値が割り当てられていない可能性があるため、エラーとする
            raise RuntimeError(
                f"問題が無限に良い解を持っています。ソルバーステータス: {pulp.LpStatus[lp.status]}"
            )
        elif status == pulp.constants.LpStatusUndefined:
            # 状態が不明な場合はエラーとする
            raise RuntimeError(
                f"問題の状態が不明です。ソルバーステータス: {pulp.LpStatus[lp.status]}"
            )
        elif status in [pulp.constants.LpStatusOptimal, pulp.constants.LpStatusNotSolved]:
            # 最適解が見つかった、またはタイムリミット到達で部分解が存在する可能性がある
            pass
        else:
            # その他のステータスは予期しないものとしてエラーとする
            raise RuntimeError(
                f"予期しないソルバーステータス: {pulp.LpStatus[lp.status]}"
            )

        # --- 結果の取得 ---
        menus: dict[int, list[int]] = {}
        for j in opt_meals:
            meal_idx = j - M  # 0始まりに変換
            menus[meal_idx] = [
                i for i in dishes
                if (pulp.value(X[i][j]) or 0.0) > 0.5
            ]

        nutritions: dict[int, dict[int, float]] = {}
        for d in range(L):
            nutritions[d] = {}
            for k in nutrients:
                total = sum(
                    prob.A[i].get(k, 0.0)
                    for p in range(3)
                    for i in menus.get(3 * d + p, [])
                )
                nutritions[d][k] = total

        return Solution(menus=menus, nutritions=nutritions, problem=prob, lp_problem=lp)
