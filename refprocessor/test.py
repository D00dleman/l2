import unittest

from refprocessor.age_parser import AgeRight
from refprocessor.common import SIGN_GT, SIGN_GTE, SIGN_LT, SIGN_LTE, ValueRange, get_sign_by_string, RANGE_IN, RANGE_LOWER, RANGE_OVER, RANGE_NEQ
from refprocessor.result_parser import ResultRight


class CheckFunctions(unittest.TestCase):
    """Проверка утилитарных функций"""

    def test_detect_age_mode(self):
        """Проверка на обнаружение режима возраста"""

        modes = (
            ("invalid", AgeRight.MODE_UNKNOWN),
            ("дней", AgeRight.MODE_DAY),
            ("день", AgeRight.MODE_DAY),
            ("дня", AgeRight.MODE_DAY),
            ("дн.", AgeRight.MODE_DAY),
            ("дн", AgeRight.MODE_DAY),
            ("д", AgeRight.MODE_DAY),
            ("д.", AgeRight.MODE_DAY),
            ("месяц", AgeRight.MODE_MONTH),
            ("месяцев", AgeRight.MODE_MONTH),
            ("месяца", AgeRight.MODE_MONTH),
            ("мес", AgeRight.MODE_MONTH),
            ("мес.", AgeRight.MODE_MONTH),
            ("м", AgeRight.MODE_MONTH),
            ("м.", AgeRight.MODE_MONTH),
            ("год", AgeRight.MODE_YEAR),
            ("года", AgeRight.MODE_YEAR),
            ("лет", AgeRight.MODE_YEAR),
            ("г", AgeRight.MODE_YEAR),
            ("г.", AgeRight.MODE_YEAR),
            ("л", AgeRight.MODE_YEAR),
            ("л.", AgeRight.MODE_YEAR),
        )

        for m in modes:
            mode = AgeRight.get_mode_by_string(m[0])
            self.assertEqual(m[1], mode, f"Режим '{mode}' для '{m[0]}' должен быть '{m[1]}'")

    def test_detect_sign(self):
        """Проверка на обнаружение знака"""

        signs = (
            ("invalid", None),
            (">", SIGN_GT),
            ("&gt;", SIGN_GT),
            ("старше", SIGN_GT),
            ("больше", SIGN_GT),
            ("более", SIGN_GT),
            (">=", SIGN_GTE),
            ("≥", SIGN_GTE),
            ("&ge;", SIGN_GTE),
            ("от", SIGN_GTE),
            ("с", SIGN_GTE),
            ("<", SIGN_LT),
            ("&lt;", SIGN_LT),
            ("младше", SIGN_LT),
            ("меньше", SIGN_LT),
            ("менее", SIGN_LT),
            ("до", SIGN_LT),
            ("<=", SIGN_LTE),
            ("≤", SIGN_LTE),
            ("&le;", SIGN_LTE),
            ("по", SIGN_LTE),
        )

        for s in signs:
            sign = get_sign_by_string(s[0])
            self.assertEqual(s[1], sign, f"Знак '{sign}' должен быть '{s[1]}'")


class ParseAgeRights(unittest.TestCase):
    """Проверка разбора строки возраста"""

    def test_default_year_constant(self):
        """Возраст в виде простого числа определяется корректно"""

        right = AgeRight("5 ")
        correct_range = ValueRange(5, 5)
        self.assertEqual(correct_range, right.age_range, f"Диапазон должен быть '{correct_range}'")
        self.assertEqual(AgeRight.MODE_YEAR, right.mode, "Режим должен быть 'year'")

    def test_all_ages(self):
        """Все возраста определяются корректно"""

        strs = ["все", "Все", " все ", ""]

        correct_range = ValueRange(0, float('inf'))

        for s in strs:
            right = AgeRight(s)
            self.assertEqual(correct_range, right.age_range, f"Диапазон должен быть '{correct_range}'")
            self.assertEqual(AgeRight.MODE_YEAR, right.mode, "Режим должен быть 'year'")

    def test_default_year_ages(self):
        """Возраст в виде простого диапазона определяется корректно"""

        strs = ["1-10", "1 - 10", " 1 - 10 "]

        correct_range = ValueRange(1, 10)

        for s in strs:
            right = AgeRight(s)
            self.assertEqual(correct_range, right.age_range, f"Диапазон должен быть '{correct_range}'")
            self.assertEqual(AgeRight.MODE_YEAR, right.mode, "Режим должен быть 'year'")

    def test_constant_age_with_mode(self):
        """Возраст в виде константного числа с режимом определяется корректно"""

        ages = [
            ["0 дней", 0, AgeRight.MODE_DAY],
            ["6 месяцев", 6, AgeRight.MODE_MONTH],
            ["5 л.", 5, AgeRight.MODE_YEAR],
            [" 100  лет", 100, AgeRight.MODE_YEAR],
        ]

        for age in ages:
            correct_range = ValueRange(age[1], age[1])
            right = AgeRight(age[0])
            self.assertEqual(correct_range, right.age_range, f"Диапазон должен быть '{correct_range}' для '{age[0]}'")
            self.assertEqual(age[2], right.mode, f"Режим должен быть 'year' для '{age[0]}'")

    def test_constant_age_with_sign_and_optional_mode(self):
        """Возраст в виде числа с опциональным режимом и направлением определяется корректно"""

        ages = [
            ["> 0 дней", (0, ")"), float("inf"), AgeRight.MODE_DAY],
            ["&gt; 0 дней", (0, ")"), float("inf"), AgeRight.MODE_DAY],
            ["больше 5 дней", (5, ")"), float("inf"), AgeRight.MODE_DAY],
            ["более 5 дней", (5, ")"), float("inf"), AgeRight.MODE_DAY],
            ["от 1 дня", (1, "]"), float("inf"), AgeRight.MODE_DAY],
            ["≥ 1 дня", (1, "]"), float("inf"), AgeRight.MODE_DAY],
            ["с 1 дня", (1, "]"), float("inf"), AgeRight.MODE_DAY],
            [">= 1 дня", (1, "]"), float("inf"), AgeRight.MODE_DAY],
            ["&ge; 1 дня", (1, "]"), float("inf"), AgeRight.MODE_DAY],
            ["до 7 дней", 0, (7, ")"), AgeRight.MODE_DAY],
            ["< 7 дней", 0, (7, ")"), AgeRight.MODE_DAY],
            ["старше 5 лет", (5, ")"), float("inf"), AgeRight.MODE_YEAR],
            ["младше 5 лет", 0, (5, ")"), AgeRight.MODE_YEAR],
            ["меньше 5 лет", 0, (5, ")"), AgeRight.MODE_YEAR],
            ["менее 5 лет", 0, (5, ")"), AgeRight.MODE_YEAR],
            ["до 20", 0, (20, ")"), AgeRight.MODE_YEAR],
            ["< 100", 0, (100, ")"), AgeRight.MODE_YEAR],
            ["&lt; 100", 0, (100, ")"), AgeRight.MODE_YEAR],
            ["≤ 100", 0, (100, "]"), AgeRight.MODE_YEAR],
            ["<= 100", 0, (100, "]"), AgeRight.MODE_YEAR],
            ["&le; 100", 0, (100, "]"), AgeRight.MODE_YEAR],
        ]

        for age in ages:
            correct_range = ValueRange(age[1], age[2])
            right = AgeRight(age[0])
            self.assertEqual(correct_range, right.age_range, f"Диапазон должен быть '{correct_range}', а не '{right.age_range}' для '{age[0]}'")
            self.assertEqual(age[3], right.mode, f"Режим должен быть '{age[3]}' для '{age[0]}'")

    def test_full_defined_range(self):
        """Проверка полностью определённого диапазона с опциональными частями"""

        ages = [
            ["10 - 20", 10, 20, AgeRight.MODE_YEAR],
            ["1 г - 2 г", 1, 2, AgeRight.MODE_YEAR],
            ["10 лет – 20 лет", 10, 20, AgeRight.MODE_YEAR],
            ["2г. – 3г.", 2, 3, AgeRight.MODE_YEAR],
            ["от 3 до 5 дней", 3, (5, ")"), AgeRight.MODE_DAY],
            ["от 3 дней до 5", 3, (5, ")"), AgeRight.MODE_DAY],
            ["от 3 месяцев до 5 месяцев", 3, (5, ")"), AgeRight.MODE_MONTH],
            ["с 3 по 5", 3, 5, AgeRight.MODE_YEAR],
        ]

        for age in ages:
            correct_range = ValueRange(age[1], age[2])
            right = AgeRight(age[0])
            self.assertEqual(correct_range, right.age_range, f"Диапазон должен быть '{correct_range}', а не '{right.age_range}' для '{age[0]}'")
            self.assertEqual(age[3], right.mode, f"Режим должен быть '{age[3]}' для '{age[0]}'")


class CheckAgeChecking(unittest.TestCase):
    """Проверка обнарпужения вхождения в AgeRight"""

    def test_in_age_right(self):
        ages = [
            ["до 5 дней", [0, 0, 0], True],
            ["от 3 до 8 дней", [4, 0, 0], True],
            ["от 3 до 10 месяцев", [0, 3, 0], True],
            ["от 3 до 10 месяцев", [1, 3, 0], True],
            ["от 7 до 11 лет", [0, 0, 10], True],
            ["от 7 до 11 лет", [1, 2, 10], True],
        ]

        for age in ages:
            right = AgeRight(age[0])
            in_range = right.test(age[1])
            self.assertEqual(age[2], in_range, f"Вхождение должно быть '{age[2]}', а не '{in_range}' для '{age[0]}' '{right.age_range}' и '{age[1]}'")

    def test_not_in_age_right(self):
        ages = [
            ["до 5 дней", [5, 0, 0], False],
            ["до 5 дней", [0, 1, 0], False],
            ["до 5 дней", [0, 0, 1], False],
            ["от 3 до 8 дней", [2, 0, 0], False],
            ["от 3 до 8 дней", [9, 0, 0], False],
            ["от 3 до 10 месяцев", [1, 0, 0], False],
            ["от 3 до 10 месяцев", [0, 2, 0], False],
            ["от 7 до 10 лет", [0, 0, 12], False],
            ["старше 8 лет", [0, 0, 8], False],
            ["< 8 лет", [0, 0, 8], False],
        ]

        for age in ages:
            right = AgeRight(age[0])
            in_range = right.test(age[1])
            self.assertEqual(age[2], in_range, f"Вхождение должно быть '{age[2]}', а не '{in_range}' для '{age[0]}' '{right.age_range}' и '{age[1]}'")


class ParseResultRights(unittest.TestCase):
    """Проверка разбора референсов результатов"""

    def test_empty(self):
        """Пустой референс должен иметь особый режим"""
        rs = ["", " "]
        for r in rs:
            right = ResultRight(r)
            self.assertEqual(ResultRight.MODE_ANY, right.mode, f"Режим должен быть '{ResultRight.MODE_ANY}' для '{r}'")

    def test_range(self):
        """Диапазон число - число"""
        rs = [
            ["10-100", 10, 100],
            ["0.55 – 0.633", 0.55, 0.633],
            ["2.0-21.0", 2.0, 21.0],
            ["10 -100", 10, 100],
            ["-10 - 100", -10, 100],
            ["-100 - -10", -100, -10],
            ["10 – 20", 10, 20],
            ["0,23 - 2,0", 0.23, 2.0],
            ["от 1 до 2", 1, (2, ")")],
        ]

        for r in rs:
            right = ResultRight(r[0])
            valid = ValueRange(r[1], r[2])
            self.assertEqual(valid, right.range, f"Диапазон должен быть '{valid}', а не '{right.range}' для '{r[0]}'")

    def test_value_from_to(self):
        """Значения от или до (больше, меньше, >=, <=)"""
        rs = [
            ["> 1.1", (1.1, ")"), float("inf"), ResultRight.MODE_NUMBER_RANGE],
            ["> 1,1", (1.1, ")"), float("inf"), ResultRight.MODE_NUMBER_RANGE],
            ["> 1", (1, ")"), float("inf"), ResultRight.MODE_NUMBER_RANGE],
            ["&gt; 1", (1, ")"), float("inf"), ResultRight.MODE_NUMBER_RANGE],
            ["больше 1", (1, ")"), float("inf"), ResultRight.MODE_NUMBER_RANGE],
            ["больше 10<sup>2</sup>", (100, ")"), float("inf"), ResultRight.MODE_NUMBER_RANGE],
            [">= 1.1", (1.1, "]"), float("inf"), ResultRight.MODE_NUMBER_RANGE],
            ["≥ 1.1", (1.1, "]"), float("inf"), ResultRight.MODE_NUMBER_RANGE],
            ["&ge; 1.1", (1.1, "]"), float("inf"), ResultRight.MODE_NUMBER_RANGE],
            ["от 1.1", (1.1, "]"), float("inf"), ResultRight.MODE_NUMBER_RANGE],
            ["< 10", float("-inf"), (10, ")"), ResultRight.MODE_NUMBER_RANGE],
            ["&lt; 10", float("-inf"), (10, ")"), ResultRight.MODE_NUMBER_RANGE],
            ["меньше 10", float("-inf"), (10, ")"), ResultRight.MODE_NUMBER_RANGE],
            ["менее 10", float("-inf"), (10, ")"), ResultRight.MODE_NUMBER_RANGE],
            ["до 10", float("-inf"), (10, ")"), ResultRight.MODE_NUMBER_RANGE],
            ["<= 10,1", float("-inf"), (10.1, "]"), ResultRight.MODE_NUMBER_RANGE],
            ["≤ 10", float("-inf"), (10, "]"), ResultRight.MODE_NUMBER_RANGE],
            ["&le; 10", float("-inf"), (10, "]"), ResultRight.MODE_NUMBER_RANGE],
            ["по 10", float("-inf"), (10, "]"), ResultRight.MODE_NUMBER_RANGE],
        ]

        for r in rs:
            right = ResultRight(r[0])
            valid = ValueRange(r[1], r[2])
            self.assertEqual(valid, right.range, f"Диапазон должен быть '{valid}', а не '{right.range}' для '{r[0]}'")
            self.assertEqual(r[3], right.mode, f"Режим должен быть '{r[3]}' для '{r[0]}'")

    def test_of_test(self):
        rs = [
            ["от 5", 5, (ResultRight.RESULT_MODE_NORMAL, RANGE_IN)],
            ["от 5", 6, (ResultRight.RESULT_MODE_NORMAL, RANGE_IN)],
            ["от 5", 4, (ResultRight.RESULT_MODE_NOT_NORMAL, RANGE_LOWER)],
            ["> 5", 5, (ResultRight.RESULT_MODE_NOT_NORMAL, RANGE_LOWER)],
            ["> 5.1", 5.2, (ResultRight.RESULT_MODE_NORMAL, RANGE_IN)],
            ["от 3 до 5.5", 5.2, (ResultRight.RESULT_MODE_NORMAL, RANGE_IN)],
            ["от 3 до 5.5", 0, (ResultRight.RESULT_MODE_NOT_NORMAL, RANGE_LOWER)],
            ["< 10", -1, (ResultRight.RESULT_MODE_NORMAL, RANGE_IN)],
            ["< 10", "9 8 7 6 5 4 3 2.2 1,1", (ResultRight.RESULT_MODE_NORMAL, RANGE_IN)],
            ["< 10", "9 8 7 6 5 4 3 2.2 1,1 10 11", (ResultRight.RESULT_MODE_NOT_NORMAL, RANGE_OVER)],
            ["< 10", "test", (ResultRight.RESULT_MODE_MAYBE, RANGE_NEQ)],
            ["test", "1", (ResultRight.RESULT_MODE_MAYBE, RANGE_NEQ)],
            [">= 10<sup>2</sup>", "10<sup>2</sup>", (ResultRight.RESULT_MODE_NORMAL, RANGE_IN)],
            ["> 10<sup>2</sup>", "10<sup>2</sup>", (ResultRight.RESULT_MODE_NOT_NORMAL, RANGE_LOWER)],
            ["до 5", "сплошь", (ResultRight.RESULT_MODE_NOT_NORMAL, RANGE_OVER)],
        ]

        for r in rs:
            right = ResultRight(r[0])
            in_range = right.test(str(r[1]))
            self.assertEqual(r[2], in_range, f"Вхождение должно быть '{r[2]}', а не '{in_range}' для '{r[0]}' '{right.range}' и '{r[1]}'")


if __name__ == '__main__':
    unittest.main()
