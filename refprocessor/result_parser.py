import re
from typing import Union, Tuple

from refprocessor.common import ValueRange, Value, get_sign_by_string, POINT_STRICT, SIGN_GT, SIGN_GTE, SIGN_LT, SIGN_LTE, RANGE_REGEXP, RANGE_IN, RANGE_NEQ, replace_pow


class ResultRight:
    MODE_NUMBER_RANGE = 'number_range'
    MODE_CONSTANT = 'constant'
    MODE_ANY = 'any'

    RESULT_MODE_NORMAL = 'normal'
    RESULT_MODE_MAYBE = 'maybe'
    RESULT_MODE_NOT_NORMAL = 'not_normal'

    def __init__(self, orig_str: str):
        orig_str = orig_str.strip().lower()
        self.range = ValueRange(0, 0)

        if not orig_str:
            self.mode = ResultRight.MODE_ANY
            return

        orig_str = replace_pow(re.sub(' +', ' ', orig_str))

        const_range = ResultRight.check_is_constant_with_sign(orig_str)

        if const_range:
            self.mode = const_range[0]
            self.range = ValueRange(const_range[1], const_range[2])
            return

        simple_range = ResultRight.check_is_range(orig_str)

        if simple_range:
            self.mode = simple_range[0]
            self.range = ValueRange(simple_range[1], simple_range[2])
            return

        self.mode = ResultRight.MODE_CONSTANT
        self.const = orig_str

    def test(self, value: str) -> Tuple[str, str]:
        if self.mode == ResultRight.MODE_ANY:
            return ResultRight.RESULT_MODE_NORMAL, RANGE_IN

        value = replace_pow(value.strip().lower().replace("''", "\""))

        if "един" in value:
            value = "1"

        if "отсутств" in value or "нет" in value:
            value = "0"

        if self.mode == ResultRight.MODE_CONSTANT:
            return (ResultRight.RESULT_MODE_NORMAL, RANGE_IN) if value == self.const else (ResultRight.RESULT_MODE_MAYBE, RANGE_NEQ)

        if "сплошь" in value.lower() or "++" in value or "+ +" in value or "++++" in value or "+" == value.strip() or "оксал ед" in value:
            value = "inf"

        numbers = re.findall(r"-?\d*[.,]\d+|-?\d+|inf", value)

        if numbers:
            for n in numbers:
                n = float(n.replace(',', '.'))
                rv = self.range.in_range(n)
                if rv != RANGE_IN:
                    return ResultRight.RESULT_MODE_NOT_NORMAL, rv
        elif value:
            return ResultRight.RESULT_MODE_MAYBE, RANGE_NEQ

        return ResultRight.RESULT_MODE_NORMAL, RANGE_IN

    @staticmethod
    def check_is_range(s: str) -> Union[bool, Tuple[str, Union[float, Value], Union[float, Value]]]:
        matched = re.match(RANGE_REGEXP, s)

        if matched:
            g = list(map(lambda x: x if not x else x.strip(), matched.groups()))

            mode = ResultRight.MODE_NUMBER_RANGE

            if g[4] == 'до':
                return mode, Value(g[1]), Value(float(g[5]), mode=POINT_STRICT)

            return mode, Value(g[1]), Value(g[5])
        return False

    @staticmethod
    def check_is_constant_with_sign(orig_str: str) -> Union[bool, Tuple[str, Value, Value]]:
        matched = re.match(r"^([\w<>≤≥&;=]+) ?(-?\d+[.,]\d+|-?\d+)$", orig_str)

        if matched:
            g = list(matched.groups())

            mode = ResultRight.MODE_NUMBER_RANGE

            sign_orig = g[0]
            sign = get_sign_by_string(sign_orig)
            if not sign:
                return False

            value = g[1]

            if sign == SIGN_GT:
                return mode, Value(value=value, mode=POINT_STRICT), Value(value=float('inf'))

            if sign == SIGN_GTE:
                return mode, Value(value=value), Value(value=float('inf'))

            if sign == SIGN_LT:
                return mode, Value(value=float('-inf')), Value(value=value, mode=POINT_STRICT)

            if sign == SIGN_LTE:
                return mode, Value(value=float('-inf')), Value(value=value)

        return False
