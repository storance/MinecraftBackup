from dateutil.relativedelta import relativedelta
from .tagger import HourlyTagger, DailyTagger, WeeklyTagger, MonthlyTagger, YearlyTagger, SnapshotTagger
from .base import RetentionPolicy, RetentionRule, DurationForever, Duration

__all__ = ["parse", "ParseError"]

_NORMALIZED_DURATIONS = {
    "second" : "seconds",
    "seconds" : "seconds",
    "minute" : "minutes",
    "minutes" : "minutes",
    "hour" : "hours",
    "hours" : "hours",
    "week" : "weeks",
    "weeks" : "weeks",
    "day" : "days",
    "days" : "days",
    "month" : "months",
    "months" : "months",
    "year" : "years",
    "years" : "years",
}

_NAME_TO_TAGGER = {
    'hourly' : HourlyTagger,
    'daily' : DailyTagger,
    'weekly' : WeeklyTagger,
    'monthly' : MonthlyTagger,
    'yearly' : YearlyTagger
}

def parse(rules):
    return RetentionPolicy([_parse_rule(i, rule) for i, rule in enumerate(rules, 1) if rule.strip()])

def _parse_rule(rule_number, rule):
    state = ParserState(rule.lower().split())
    tagger = _parse_tagger(rule_number, state)

    if not state.has_next():
        raise ParseError(rule_number, "Missing required keep duration.")

    prev_token = state.last()
    next_token = state.next()
    if next_token != 'keep':
        raise ParseError(rule_number, "Unexpected token {} following {}; expected 'keep'.".format(
            next_token, prev_token))
    
    # skip the optional for
    if state.peek() == 'for':
        state.next()

    duration = _parse_duration(rule_number, state)

    #  check for extra garbage
    if state.has_next():
        prev_token = state.last()
        next_token = state.next()
        raise ParseError(rule_number, "Unexpected token {} following {}; expected end of rule.".format(
            next_token, prev_token))

    return RetentionRule(tagger, duration)

def _parse_tagger(rule_number, state):
    if state.peek() == 'keep':
        return SnapshotTagger()

    raw_timeframe = state.next()

    latest = False
    if raw_timeframe == 'latest':
        latest = True
    elif raw_timeframe != 'oldest':
        raise ParseError(rule_number, "Unsupported backup tag '{}' specified. Must be latest or oldest".format(
            raw_timeframe))

    raw_tag = state.next()
    tagger = _NAME_TO_TAGGER.get(raw_tag)

    if tagger is None:
        raise ParseError(rule_number, "Unsupported time granularity '{}' specified.".format(raw_tag))

    return tagger(latest)


def _parse_duration(rule_number, state):
    if not state.has_next():
        raise ParseError(rule_number, "Missing required keep duration.")

    raw_value = state.next()

    if raw_value == 'forever':
        return DurationForever()

    try:
        value = int(raw_value)
    except ValueError:
        raise ParseError(rule_number, "Keep duration '{}' is not a valid number.".format(raw_value))

    if value <= 0:
        raise ParseError(rule_number, "Keep duration '{}' is less than or equal to zero.".format(value))

    if not state.has_next():
        raise ParseError(rule_number, "No units for the keep duration were specified.")

    raw_units = state.next()
    units = _NORMALIZED_DURATIONS.get(raw_units)
    if not units:
        raise ParseError(rule_number, "Unsupported units '{}' specified for the keep duration.".format(raw_units))

    return Duration(relativedelta(**{units : value}))

class ParserState(object):
    def __init__(self, parts):
        self.parts = parts
        self.position = 0

    def __iter__(self):
        return self

    def next(self):
        if not self.has_next():
            raise StopIteration()

        self.position += 1
        return self.parts[self.position-1]

    def has_next(self):
        return self.position < len(self.parts)

    def has_prev(self):
        return self.position > 0

    def prev(self):
        if not self.has_prev():
            return None

        self.position -= 1
        return self.parts[self.position]

    def peek(self):
        if not self.has_next():
            return None

        return self.parts[self.position]

    def last(self):
        if not self.has_prev():
            return None

        return self.parts[self.position-1]

    @property
    def remaining(self):
        return self.parts[self.position:]

class ParseError(Exception):
    def __init__(self, rule_number, error):
        super(ParseError, self).__init__()
        self.rule_number = rule_number
        self.error = error

    def __str__(self):
        return "Rule #{}: {}".format(self.rule_number, self.error)
