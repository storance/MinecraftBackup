import datetime
from itertools import chain
from .. import meta
from dateutil.tz import tzutc

__all__ = ["RetentionPolicy", "RetentionRule", "Duration", "DurationForever"]

class RetentionPolicy(object):
    def __init__(self, rules):
        self.rules = rules
        self._validate_rules()

    def _validate_rules(self):
        last_rule = None
        for i, rule in enumerate(self.rules, 1):
            if not rule.is_higher_granularity(last_rule):
                raise ValueError("Rule #{}: Rule must apply to a larger time granularity than the previous rule.".
                    format(i))

            last_rule = rule

    def apply(self, backups):
        purge = {}
        last_rule = None
        
        grouped_backups = _group_backups_by_tag(backups)
        for rule in self.rules:
            # find backups purged by the previous rule that should be tagged with this rule's tag
            if last_rule is not None:
                retagged_backups = rule.find_retag_candidate(purge[last_rule.tag], backups)
                for backup in retagged_backups:
                    purge[last_rule.tag].remove(backup)
                    grouped_backups[rule.tag].add(backup)

            # purge expired backups
            purge[rule.tag] = set()
            for backup in grouped_backups[rule.tag].copy():
                if rule.is_expired(backup):
                    grouped_backups[rule.tag].remove(backup)
                    purge[rule.tag].add(backup)

            # check if any time bucket has multiple backups and purge the latest/oldest depending on the policy
            duplicates = rule.find_duplicates(grouped_backups[rule.tag])
            for backup in duplicates:
                grouped_backups[rule.tag].remove(backup)
                purge[rule.tag].add(backup)

            last_rule = rule

        return (list(chain.from_iterable(grouped_backups.values())), list(chain.from_iterable(purge.values())))

    def __eq__(self, other):
        if isinstance(other, RetentionPolicy):
            return self.rules == other.rules
        return False

    def __repr__(self):
        return "RetentionPolicy{{rules=[{}]}}".format(','.join([repr(rule) for rule in self.rules]))

def _group_backups_by_tag(backups):
    grouped_backups = {
        meta.TAG_SNAPSHOT : set(),
        meta.TAG_HOURLY : set(),
        meta.TAG_DAILY : set(),
        meta.TAG_WEEKLY : set(),
        meta.TAG_MONTHLY : set(),
        meta.TAG_YEARLY : set()
    }

    for backup in backups:
        grouped_backups[backup.tag].add(backup)

    return grouped_backups

class RetentionRule(object):
    def __init__(self, tagger, duration):
        self.tagger = tagger
        self.duration = duration

    @property
    def tag(self):
        return self.tagger.tag

    def find_retag_candidate(self, candidates, all_backups):
        if not self.tagger.support_retag:
            return []

        grouped_backups = self.tagger.group_by_time(all_backups)
        return [candidate.retag(self.tag) for candidate in candidates if self.tagger.should_retag(
                candidate, grouped_backups)]

    def find_duplicates(self, backups):
        duplicates = []
        grouped_backups = self.tagger.group_by_time(backups)

        for backups_for_time in grouped_backups.values():
            if len(backups_for_time) > 1:
                duplicates.extend(backups_for_time[1:])

        return duplicates

    def is_expired(self, backup):
        return self.duration.is_expired(backup)

    def is_higher_granularity(self, other):
        if other is None:
            return True
        return self.tagger.is_higher_granularity(other.tagger)

    def __eq__(self, other):
        if isinstance(other, RetentionRule):
            return self.tagger == other.tagger and self.duration == other.duration
        return False

    def __repr__(self):
        return "RetentionRule{{tagger={},duration={}}}".format(self.tagger, self.duration)


class BaseDuration(object):
    def is_expired(self, backup):
        raise NotImplementedError()

class Duration(BaseDuration):
    def __init__(self, relative_delta):
        self.relative_delta = relative_delta

    def is_expired(self, backup):
        return backup.time + self.relative_delta < datetime.datetime.now(tzutc())

    def __eq__(self, other):
        if isinstance(other, Duration):
            return self.relative_delta == other.relative_delta
        return False

    def __repr__(self):
        return "Duration{{relative_delta={}}}".format(repr(self.relative_delta))


class DurationForever(BaseDuration):
    def is_expired(self, backup):
        return False

    def __eq__(self, other):
        return isinstance(other, DurationForever)

    def __repr__(self):
        return "DurationForever{{}}"

