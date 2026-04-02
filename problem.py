"""献立の最適化の問題インスタンスを定義するモジュール"""


class Problem:
    """献立の最適化の問題インスタンスを定義するクラス。

    インデックス規則:
        - 食事インデックス j は 0 始まりの連番。
        - j ∈ {0, ..., M-1}   : 最適化開始前の過去食事（定数として与える）
        - j ∈ {M, ..., M+3L-1}: 最適化対象の食事（3食/日 × L 日）
        - 日インデックス d ∈ {0, ..., L-1} は食事 {M+3d, M+3d+1, M+3d+2} に対応。
    """

    def __init__(
        self,
        M: int,
        L: int,
        N: dict[int, dict[int, float]],
        A: dict[int, dict[int, float]],
        D: dict[int, int],
        F: dict[int, int],
        P: int,
        C: list[tuple[int, int]],
        alpha_p: dict[int, float],
        alpha_m: dict[int, float],
        dish_names: dict[int, str],
        nutrient_names: dict[int, str],
        past_meals: dict[int, list[int]] | None = None,
        time_limit: float = 10.0,
    ) -> None:
        """Problemクラスのコンストラクタ。

        Args:
            M: 何食前の献立まで考慮するかを表す定数。
            L: 献立を作成する日数（総食事数は 3L）。
                N: 日番号 -> {栄養素ID: 目標値} のマッピング。
                    N[d][k] = d日目の栄養素kの目標値。
            A: 料理 i に含まれる栄養素 k の量。A[i][k] = 量。
               栄養素 k が含まれない場合は A[i] に k を含めなくてよい（0 として扱う）。
            D: 料理 i の許容頻度の期間（食事数）。D[i] = 期間。
            F: 料理 i の D[i] 食間での許容出現回数。F[i] = 回数。
            P: 1回の食事における最低品目数。
            C: 同一食事への同時割り当てを禁止する料理ペアのリスト。
               例: [(1, 3)] は料理1と料理3が同じ食事に入らないことを示す。
            alpha_p: 栄養素IDをキーとする超過コスト係数。alpha_p[k] = 係数。
            alpha_m: 栄養素IDをキーとする欠乏コスト係数。alpha_m[k] = 係数。
            dish_names: 料理ID -> 料理名のマッピング。
            nutrient_names: 栄養素ID -> 栄養素名のマッピング。
            past_meals: 過去の食事履歴。
                        {食事インデックス j: 料理IDのリスト} (0 <= j <= M-1)。
                        省略時は全て空（料理なし）として扱う。
            time_limit: ソルバーのタイムリミット（秒）。デフォルト値は 10.0 秒。
        """
        if set(N.keys()) != set(range(L)):
            raise ValueError("N には 0 から L-1 までの全日番号の目標値が必要です。")

        nutrient_key_set: set[int] | None = None
        for day, day_targets in N.items():
            if nutrient_key_set is None:
                nutrient_key_set = set(day_targets.keys())
                continue
            if set(day_targets.keys()) != nutrient_key_set:
                raise ValueError(
                    f"N[{day}] の栄養素キーが他の日と一致していません。"
                )

        self.M = M
        self.L = L
        self.N = N
        self.A = A
        self.D = D
        self.F = F
        self.P = P
        self.C = C
        self.alpha_p = alpha_p
        self.alpha_m = alpha_m
        self.dish_names = dish_names
        self.nutrient_names = nutrient_names
        self.past_meals: dict[int, list[int]] = past_meals if past_meals is not None else {}
        self.time_limit = time_limit

